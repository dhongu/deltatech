from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_auto_accounts(self):
        self.ensure_one()

        valuation_class = self.product_id.product_tmpl_id.valuation_class_id.id
        valuation_area = (
            self.company_id.valuation_area_id.id if hasattr(self.company_id, "valuation_area_id") else False
        )
        account_modifier = self.picking_id.picking_type_id.account_modifier_id.id if self.picking_id else False
        transaction_key = self._compute_transaction_key()

        rule = self.env["product.account.determination"].search(
            [
                ("transaction_key", "=", transaction_key),
                ("account_modifier_id", "=", account_modifier),
                ("valuation_class_id", "=", valuation_class),
                ("valuation_area_id", "=", valuation_area),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        )

        return {
            "debit": rule.debit_account_id.id if rule else False,
            "credit": rule.credit_account_id.id if rule else False,
        }

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
