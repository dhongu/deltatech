import logging

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_accounting_data_for_valuation(self):
        if not self.product_id.valuation_class_id:
            return super()._get_accounting_data_for_valuation()

        valuation_area = self.company_id.valuation_area_id
        if self.warehouse_id.valuation_area_id:
            valuation_area = self.warehouse_id.valuation_area_id
        if self.location_id.valuation_area_id:
            valuation_area = self.location_id.valuation_area_id

        if not valuation_area:
            raise UserError("Valuation area is not defined")

        journal_id = valuation_area.stock_journal_id.id
        if not journal_id:
            raise UserError("Stock journal is not defined for the valuation area")

        picking_type = self.picking_type_id
        transaction_key = self._compute_transaction_key()
        account_modifier = self.env["account.modifier"]
        if picking_type:
            account_modifier = picking_type.account_modifier_id

        _get_rule_account = self.env["product.account.determination"]._get_rule_account
        rule = _get_rule_account(
            valuation_area=valuation_area,
            valuation_class=self.product_id.valuation_class_id,
            transaction_key="BSX",
            account_modifier=account_modifier,
            company=self.company_id,
        )

        acc_valuation = rule.acc_valuation_id.id

        rule = _get_rule_account(
            valuation_area=valuation_area,
            valuation_class=self.product_id.valuation_class_id,
            transaction_key=transaction_key,
            account_modifier=account_modifier,
            company=self.company_id,
        )
        acc_src = rule.acc_src_id.id
        acc_dest = rule.acc_dest_id.id

        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_vals(self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id,
                                   cost):
        self.ensure_one()
        if credit_account_id == debit_account_id or not credit_account_id or not debit_account_id:
            return {}
        return super()._prepare_account_move_vals(credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost)


    def _compute_transaction_key(self):
        source_usage = self.location_id.usage
        dest_usage = self.location_dest_id.usage

        if source_usage == "supplier" and dest_usage == "internal":
            return "WRX"
        elif source_usage == "internal" and dest_usage == "customer":
            return "VAX"
        elif source_usage == "internal" and dest_usage == "internal":
            return "ZTR"
        else:
            return "GBB"
