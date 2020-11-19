from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    packaging_material_ids = fields.One2many("product.packaging_material", "product_tmpl_id", string="Packaging materials")


class ProductPackagingMaterial(models.Model):
    _name = "product.packaging_material"
    _description = "Model for one2many: packaging_materials_ids"

    product_tmpl_id = fields.Many2one("product.template")
    materials_selection = fields.Selection([("plastic", "Plastic"), ("wood", "Wood"), ("paper", "Paper"), ("pet", "Pet")])
    qty = fields.Float(string="Quantity", default=0)
