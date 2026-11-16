# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    include_image_line = fields.Boolean(
        related="company_id.include_image_line",
        string="Include image",
        readonly=False,
        help="Include the product image on the sale order lines",
    )
