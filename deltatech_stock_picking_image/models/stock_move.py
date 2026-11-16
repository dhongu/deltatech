# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    product_image = fields.Image(
        string="Image",
        related="product_id.image_128",
        readonly=True,
        help="Product image (variant image when the product has variants)",
    )
