# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    indexnow_enabled = fields.Boolean(related="website_id.indexnow_enabled", readonly=False)
    indexnow_key = fields.Char(related="website_id.indexnow_key", readonly=False)
    indexnow_key_url = fields.Char(related="website_id.indexnow_key_url")
    indexnow_last_run = fields.Datetime(related="website_id.indexnow_last_run")
    indexnow_last_result = fields.Char(related="website_id.indexnow_last_result")

    def action_indexnow_submit_all(self):
        self.ensure_one()
        return self.website_id.action_indexnow_submit_all()
