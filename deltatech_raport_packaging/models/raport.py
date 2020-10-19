from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    product_ids = fields.One2many("product.packaging.material", "product_tmpl_id", string="Packaging materials")


class ProductPackagingMaterial(models.Model):
    _name = "product.packaging.material"
    _description = "Model for one2many: products_ids"

    product_tmpl_id = fields.Many2one("product.template")
    type = fields.Selection([("plastic", "Plastic"), ("wood", "Wood"), ("paper", "Paper"), ("pet", "Pet")])
    qty = fields.Float(string="Quantity", default=0)
