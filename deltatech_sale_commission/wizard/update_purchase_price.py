# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models
from odoo.exceptions import AccessError

from .commission_compute import PAID_STATES


class CommissionUpdatePurchasePrice(models.TransientModel):
    _name = "commission.update.purchase.price"
    _description = "Update purchase price"

    for_all = fields.Boolean(string="For all lines")
    price_from_doc = fields.Boolean(string="Price from delivery", default=True)

    invoice_line_ids = fields.Many2many(
        "sale.margin.report",
        "commission_update_purchase_price_inv_rel",
        "compute_id",
        "invoice_line_id",
        string="Account invoice line",
    )

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("id", "in", active_ids)]
        else:
            domain = [("payment_state", "in", PAID_STATES), ("commission", "=", 0.0)]
        res = self.env["sale.margin.report"].search(domain)
        defaults["invoice_line_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_compute(self):
        # the cost is written with sudo on the invoice lines, so only the commission managers
        # may run it (the wizard access is also limited to them)
        if not self.env.user.has_group("deltatech_sale_commission.group_commission_manager"):
            raise AccessError(self.env._("Only a Commission Manager can update the purchase price."))
        if self.for_all:
            lines = self.env["sale.margin.report"].search([])
        else:
            lines = self.invoice_line_ids

        for line in lines:
            invoice_line = self.env["account.move.line"].sudo().browse(line.id)
            purchase_price = 0.0

            if self.price_from_doc:
                # price from delivery, or the product cost when there is none; 0 on a credit
                # note without a return of goods
                purchase_price = invoice_line.get_purchase_price()
                if purchase_price or invoice_line.move_id.move_type == "out_refund":
                    invoice_line.write({"purchase_price": purchase_price})

            elif invoice_line.product_id.standard_price > 0:
                invoice_line.write({"purchase_price": invoice_line.product_id.standard_price})
        return True
