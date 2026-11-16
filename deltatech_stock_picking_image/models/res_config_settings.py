# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hide_picking_image_pdf = fields.Boolean(
        related="company_id.hide_picking_image_pdf",
        readonly=False,
    )
