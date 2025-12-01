# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com>
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    rfq_ids = fields.One2many("purchase.order", "quote_id", string="RFQ", readonly=True)
    rfq_count = fields.Integer(string="RFQ Count", compute="_compute_rfq_count")

    def _compute_rfq_count(self):
        for order in self:
            order.rfq_count = len(order.rfq_ids)

    def action_create_rfq(self):
        """
        Open the Purchase Order form in create mode, prefilled with lines
        derived from eligible sale order lines. The user will manually select
        the vendor and save the RFQ (draft PO).
        """
        self.ensure_one()
        if not self.order_line:
            raise UserError(self.env._("There are no lines on this quotation."))

        # Prepare default order lines from SO lines
        default_lines = []
        for so_line in self.order_line.filtered(
            lambda l: not l.display_type and l.product_id and l.product_id.purchase_ok
        ):
            qty = so_line.product_uom_qty
            if qty <= 0:
                continue
            name = so_line.name or so_line.product_id.display_name
            default_lines.append(
                (
                    0,
                    0,
                    {
                        "name": name,
                        "product_id": so_line.product_id.id,
                        "product_uom_id": so_line.product_uom_id.id,
                        "product_qty": qty,
                        # leave price_unit to be computed/filled by buyer/vendor
                        # taxes will be computed by onchange in the form
                    },
                )
            )

        if not default_lines:
            raise UserError(
                self.env._("No eligible line for purchase (products without purchase_ok or quantity <= 0).")
            )

        action = self.env.ref("purchase.purchase_form_action").read()[0]
        action.update(
            {
                "view_mode": "form",
                "views": [(self.env.ref("purchase.purchase_order_form").id, "form")],
                "context": {
                    **self.env.context,
                    "default_origin": self.name,
                    "default_company_id": self.company_id.id,
                    "default_quote_id": self.id,
                    "default_order_line": default_lines,
                },
            }
        )
        return action

    def action_view_rfq(self):
        self.ensure_one()
        action = self.env.ref("purchase.purchase_form_action").read()[0]
        action.update(
            {
                "domain": [("quote_id", "=", self.id)],
                "context": dict(self.env.context, search_default_quote_id=self.id),
            }
        )
        if self.rfq_count == 1 and self.rfq_ids:
            action.update(
                {
                    "view_mode": "form,list",
                    "res_id": self.rfq_ids.id,
                    "views": [(self.env.ref("purchase.purchase_order_form").id, "form")],
                }
            )
        return action
