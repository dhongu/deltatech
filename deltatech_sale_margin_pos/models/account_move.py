# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _get_refund_purchase_price_from_invoice(self):
        """Cost of a credit note issued from a Point of Sale return.

        When the sale was a receipt (not invoiced) and the customer asks for an invoice on the
        return, the credit note reverses no invoice and has no sale order line, so the base rule
        finds no cost. The Point of Sale already costed the goods that came back, at the cost of
        the original sale, so the unit cost is taken from the order lines of the return.
        """
        purchase_price = super()._get_refund_purchase_price_from_invoice()
        if purchase_price or self.move_id.reversed_entry_id or not self.product_id:
            return purchase_price
        pos_lines = self.move_id.sudo().pos_order_ids.lines.filtered(
            lambda line: line.product_id == self.product_id and line.is_total_cost_computed
        )
        qty = sum(pos_lines.mapped("qty"))
        if not qty:
            return purchase_price
        # the Point of Sale costs the product unit: express it in the unit of the invoice line
        unit_cost = abs(sum(pos_lines.mapped("total_cost")) / qty)
        product_uom = self.product_id.uom_id
        if self.product_uom_id and self.product_uom_id != product_uom:
            unit_cost = product_uom._compute_price(unit_cost, self.product_uom_id)
        return unit_cost
