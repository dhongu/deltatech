# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    llms_txt_enabled = fields.Boolean(related="website_id.llms_txt_enabled", readonly=False)
    llms_txt_summary = fields.Text(related="website_id.llms_txt_summary", readonly=False)
    llms_txt_details = fields.Text(related="website_id.llms_txt_details", readonly=False)
    llms_txt_custom = fields.Text(related="website_id.llms_txt_custom", readonly=False)
