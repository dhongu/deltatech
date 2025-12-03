# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


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
            domain = [("state", "=", "paid"), ("commission", "=", 0.0)]
        res = self.env["sale.margin.report"].search(domain)
        defaults["invoice_line_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_compute(self):
        if self.for_all:
            lines = self.env["sale.margin.report"].search([])
        else:
            lines = self.invoice_line_ids

        for line in lines:
            invoice_line = self.env["account.move.line"].sudo().browse(line.id)
            purchase_price = 0.0

            if self.price_from_doc:
                purchase_price = invoice_line.get_purchase_price()

                if not purchase_price:
                    if invoice_line.product_id:
                        if invoice_line.product_id.standard_price > 0:
                            purchase_price = invoice_line.product_id.standard_price

            else:
                if invoice_line.product_id:
                    if invoice_line.product_id.standard_price > 0:
                        purchase_price = invoice_line.product_id.standard_price

            if purchase_price:
                invoice_line.write({"purchase_price": purchase_price})
        return True
