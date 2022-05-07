# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountInvoice(models.Model):
    _inherit = "account.move"

    packaging_material_ids = fields.One2many("packaging.invoice.material", "invoice_id", string="Packaging materials")

    def refresh_packaging_material(self):
        lines = []
        for invoice in self:
            if not invoice.packaging_material_ids:
                qty = {}
                qty_packaging = {}

                products = self.env["product.product"]
                for item in invoice.invoice_line_ids:
                    products |= item.product_id
                    if item.product_id.id in qty:
                        qty[item.product_id.id] += item.quantity
                    else:
                        qty[item.product_id.id] = item.quantity

                for product in products:
                    for packaging_material in product.product_tmpl_id.packaging_material_ids:
                        q = qty_packaging.get(packaging_material.material_type, 0.0)
                        qty_packaging[packaging_material.material_type] = q + qty[product.id] * packaging_material.qty

                for material_type in qty_packaging:
                    lines += [
                        {"invoice_id": invoice.id, "material_type": material_type, "qty": qty_packaging[material_type]}
                    ]

                self.env["packaging.invoice.material"].create(lines)


    def action_invoice_open(self):
        res = super(AccountInvoice, self).action_invoice_open()
        for invoice in self:
            invoice.refresh_packaging_material()
        return res


class InvoicePackagingMaterial(models.Model):
    _name = "packaging.invoice.material"
    _description = "Packaging materials in invoice"

    invoice_id = fields.Many2one("account.move")
    material_type = fields.Selection([("plastic", "Plastic"), ("wood", "Wood"), ("paper", "Paper"), ("pet", "Pet")])
    qty = fields.Float(string="Quantity")
