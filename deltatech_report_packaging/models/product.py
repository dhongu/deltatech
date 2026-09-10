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
    # The same product can be packed one way by the vendor and another way when it
    # is shipped to the customer, so the quantity is kept per direction.
    qty_purchase = fields.Float(string="Purchase quantity", default=0.0)
    qty_sale = fields.Float(string="Sale quantity", default=0.0)

    def _get_qty(self, direction):
        """Quantity used for the given direction ("purchase" or "sale")."""
        self.ensure_one()
        return self.qty_purchase if direction == "purchase" else self.qty_sale
