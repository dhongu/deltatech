from odoo import models


class RaportPackaging(models.TransientModel):
    _name = "raport_packaging_materials"
    _description = "Wizard"

    def do_raport(self):
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
