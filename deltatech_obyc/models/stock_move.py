import logging

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_valuation_area(self):
        valuation_area = self.company_id.valuation_area_id
        if self.warehouse_id.valuation_area_id:
            valuation_area = self.warehouse_id.valuation_area_id
        if self.location_id.valuation_area_id and self.location_id.usage == "internal":
            valuation_area = self.location_id.valuation_area_id
        if self.location_dest_id.valuation_area_id and self.location_dest_id.usage == "internal":
            valuation_area = self.location_dest_id.valuation_area_id
        if self.location_id.usage == "internal" and self.location_dest_id.usage == "internal":
            if self.location_id.valuation_area_id != self.location_dest_id.valuation_area_id:
                raise UserError(
                    _("Source and destination locations must have the same valuation area for internal moves.")
                )
        if not valuation_area:
            raise UserError(_("Valuation area is not defined"))
        return valuation_area

    def _get_accounting_data_for_valuation(self):
        if not self.product_id.valuation_class_id:
            return super()._get_accounting_data_for_valuation()

        valuation_area = self._get_valuation_area()

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
            transaction_key=transaction_key,
            account_modifier=account_modifier,
            company=self.company_id,
        )
        acc_src = rule.acc_src_id.id
        acc_dest = rule.acc_dest_id.id
        acc_valuation = rule.acc_valuation_id.id

        return journal_id, acc_src, acc_dest, acc_valuation

    def _prepare_account_move_vals(
        self, credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost
    ):
        self.ensure_one()
        if credit_account_id == debit_account_id:
            return False
        vals =  super()._prepare_account_move_vals(
            credit_account_id, debit_account_id, journal_id, qty, description, svl_id, cost
        )
        if self.company_id.account_storno  and  self.origin_returned_move_id:
            vals["is_storno"] = True
        return vals


    def _account_entry_move(self, qty, description, svl_id, cost):
        if not qty:
            self = self.with_context(price_difference=True)
        am_vals_list = super()._account_entry_move(qty, description, svl_id, cost)
        for am_vals in am_vals_list:
            if not am_vals:
                am_vals_list.remove(am_vals)

        return am_vals_list

    def _compute_transaction_key(self):
        source_usage = self.location_id.usage
        dest_usage = self.location_dest_id.usage


        match source_usage, dest_usage:
            # Purchase transactions
            case "supplier", "internal":
                tr_key = "stock_receipt"  # Receipt from supplier
            case "supplier", "transit":
                tr_key = "stock_receipt"  # Receipt from supplier
            case "internal", "supplier":
                tr_key = "return_to_supplier"  # Return to supplier
            case "transit", "supplier":
                tr_key = "return_to_supplier"  # Return to supplier

            # Sale transactions
            case "internal", "customer":
                tr_key = "stock_delivery"  # Delivery to customer
            case "customer", "internal":
                tr_key = "return_from_customer"  # Return from customer
            case "supplier", "customer":
                tr_key = "dropship"  # Drop shipment from supplier to customer
            case "customer", "supplier":
                tr_key = "dropship_return"  # Return from customer to supplier (if applicable)

            # Internal transfers
            case "internal", "internal":
                tr_key = "internal_transfer"
            case "internal", "transit":
                tr_key = "internal_transfer_out"
            case "transit", "internal":
                tr_key = "internal_transfer_in"

            # Inventory adjustments
            case "internal", "inventory":
                tr_key = "inventory_adjustment_plus"
            case "inventory", "internal":
                tr_key = "inventory_adjustment_minus"

            # Production transactions
            case "internal", "production":
                tr_key = "production_issue"  # Issue to production
            case "production", "internal":
                tr_key = "production_receipt" # Receipt from production
            case _:
                tr_key = False

        if not tr_key:
            raise UserError(
                _(  f"Transaction key could not be determined for the move from {source_usage} to {dest_usage}."
                )
            )
        if self.env.context.get("price_difference"):
            # If the context indicates a price difference, we use a specific transaction key
            tr_key = "price_difference"
        return tr_key
