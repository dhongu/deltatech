# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    include_image_line = fields.Boolean(
        string="Include image", help="Include the product image on the sale order lines", default=True
    )
