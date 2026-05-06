from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_placeholder_image = fields.Image(
        related="website_id.product_placeholder_image",
        readonly=False,
        string="Product Placeholder Image",
        help="Default image used for products without an image",
    )
