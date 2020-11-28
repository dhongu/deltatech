from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    packaging_material_ids = fields.One2many(
        "product.packaging_material", "product_tmpl_id", string="Packaging materials"
    )


class ProductPackagingMaterial(models.Model):
    _name = "product.packaging_material"
    _description = "Packaging materials"

    product_tmpl_id = fields.Many2one("product.template")
    material_type = fields.Selection([("plastic", "Plastic"), ("wood", "Wood"), ("paper", "Paper"), ("pet", "Pet")])
    qty = fields.Float(string="Quantity")
