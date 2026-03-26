import uuid

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cron_webhook_token = fields.Char(
        string="Global Webhook Token", config_parameter="deltatech_cron_monitor_webhook.global_token"
    )

    def action_generate_cron_webhook_token(self):
        self.cron_webhook_token = str(uuid.uuid4())
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Token Generated",
                "message": "A new global token has been generated. Remember to save settings.",
                "type": "success",
                "sticky": False,
            },
        }
