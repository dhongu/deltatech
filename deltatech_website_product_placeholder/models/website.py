from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    product_placeholder_image = fields.Image(
        "Product Placeholder Image", help="Default image used for products without an image"
    )
