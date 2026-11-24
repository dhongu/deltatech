# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        # _post, not action_post: mass confirmation and scheduled auto-posting go through here too
        to_check = self
        if soft:
            # with soft=True, Odoo postpones the entries dated in the future instead of posting them
            today = fields.Date.context_today(self)
            to_check = self.filtered(lambda move: move.date <= today)
        to_check._check_storable_line_source()
        return super()._post(soft=soft)

    def _check_storable_line_source(self):
        for move in self:
            # Point of Sale invoices come from the cash register, with their own delivery
            if "pos_order_ids" in move._fields and move.pos_order_ids:
                continue
            storable_lines = move.invoice_line_ids.filtered(lambda line: line.product_id.is_storable)
            if move.is_sale_document(include_receipts=True) and move.company_id.check_storable_sale_source:
                lines = storable_lines.filtered(lambda line: not line.sale_line_ids)
                if lines:
                    raise UserError(
                        self.env._(
                            "%(move)s: storable products can be invoiced only from a sale order. "
                            "Lines without a sale order: %(products)s",
                            move=move.display_name,
                            products=", ".join(lines.product_id.mapped("display_name")),
                        )
                    )
            if move.is_purchase_document(include_receipts=True) and move.company_id.check_storable_purchase_source:
                lines = storable_lines.filtered(lambda line: not line.purchase_line_id)
                if lines:
                    raise UserError(
                        self.env._(
                            "%(move)s: storable products can be billed only from a purchase order. "
                            "Lines without a purchase order: %(products)s",
                            move=move.display_name,
                            products=", ".join(lines.product_id.mapped("display_name")),
                        )
                    )
