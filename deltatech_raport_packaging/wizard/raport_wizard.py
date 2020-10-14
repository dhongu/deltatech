from odoo import _, api, fields, models


class Raportwizard1(models.TransientModel):
    _name = "raport_wizard"
    _description = "Wizard"

    @api.model
    def _get_default_product_id(self):
        active_ids = self.env.context.get("active_ids", False)
        products = self.env["product.product"]
        qty = {}
        if active_ids:
            invoice = self.env["account.move"].browse(active_ids)
            for item in invoice.invoice_line_ids:
                products |= item.product_id
                if item.product_id in qty:
                    qty[product.id] += item.quantity
                else:
                    qty[product.id] = item.quantity

    active_ids = fields.Many2many("account.move", string="Active_ids", default=_get_default_product_id)
