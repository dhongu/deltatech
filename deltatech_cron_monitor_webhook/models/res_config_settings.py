import secrets

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cron_webhook_secret = fields.Char(
        string="Master Webhook Secret", config_parameter="deltatech_cron_monitor_webhook.master_secret"
    )
    cron_webhook_verify_signature = fields.Boolean(
        string="Verify Webhook Signature",
        config_parameter="deltatech_cron_monitor_webhook.verify_signature",
        default=True,
    )

    def action_generate_cron_webhook_secret(self):
        self.cron_webhook_secret = secrets.token_urlsafe(32)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Secret Key Generated",
                "message": "A new secret key has been generated. Remember to save settings.",
                "type": "success",
                "sticky": False,
            },
        }
