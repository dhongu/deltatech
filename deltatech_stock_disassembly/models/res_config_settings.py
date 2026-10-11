# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    disassembly_allow_reclassification = fields.Boolean(
        related="company_id.disassembly_allow_reclassification", readonly=False
    )
