from odoo import fields, models

from ..constants import PACKAGING_MATERIAL_TYPES


class ProductTemplate(models.Model):
    _inherit = "product.template"

    packaging_material_ids = fields.One2many(
        "packaging.product.material",
        "product_tmpl_id",
        string="Packaging materials",
    )


class ProductPackagingMaterial(models.Model):
    _name = "packaging.product.material"
    _description = "Packaging material used for a product"
    _order = "material_type, id"

    product_tmpl_id = fields.Many2one(
        "product.template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    material_type = fields.Selection(PACKAGING_MATERIAL_TYPES, required=True)
    qty = fields.Float(string="Quantity", required=True)
