from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = "product.category"

    overhead_amount = fields.Float(
        string="Overhead", help="For Value Overhead percent enter % ratio between 0-1.", default="0.0"
    )
