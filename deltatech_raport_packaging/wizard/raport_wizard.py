from odoo import models, fields


class RaportPackaging(models.TransientModel):
    _name = "raport_packaging_materials"
    _description = "Wizard"

    def do_raport(self):
        active_ids = self.env.context.get("active_ids", False)
        products = self.env["product.product"]
        qty_packaging = {'wood': 1, 'pet': 1, 'plastic': 1, 'paper': 1}
        qty_packaging_result = {'wood': 1, 'pet': 1, 'plastic': 1, 'paper': 1}
        qty = {}
        if active_ids:
            invoice = self.env["account.move"].browse(active_ids)
            for item in invoice.invoice_line_ids:
                products |= item.product_id
                if item.product_id in qty:
                    qty[products.id] += item.quantity
                else:
                    qty[products.id] = item.quantity

            for product in products:
                for i in product.packaging_material_ids:
                    qty_packaging[i.materials_selection] = i.qty

            for k, v in qty_packaging_result.items():
                for value in qty.values():
                    qty_packaging_result[k] = round(v * value)





