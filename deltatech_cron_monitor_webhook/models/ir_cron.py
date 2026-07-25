import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    # Webhook Integration
    enable_webhook = fields.Boolean("Enable Webhook", copy=False)
    webhook_code = fields.Char(
        "Webhook Code",
        copy=False,
        help="Unique code for this webhook",
    )
    webhook_url = fields.Char("Webhook URL", compute="_compute_webhook_url")

    _webhook_code_unique = models.Constraint(
        "unique(webhook_code)",
        "Webhook Code must be unique!",
    )

    @api.depends("webhook_code")
    def _compute_webhook_url(self):
        ConfigParam = self.env["ir.config_parameter"].sudo()
        base_url = ConfigParam.get_param("web.base.url")
        global_token = ConfigParam.get_param("deltatech_cron_monitor_webhook.global_token")
        for cron in self:
            if cron.webhook_code:
                url = f"{base_url}/cron/webhook/{cron.webhook_code}"
                if global_token:
                    url += f"?token={global_token}"
                cron.webhook_url = url
            else:
                cron.webhook_url = False

    def _log_execution(self, status, duration, error=None, traceback_text=None):
        pass

    def _send_alert(self, error_message):
        pass

    def _healthcheck_ping(self, status="success"):
        pass

    def action_reset_statistics(self):
        pass
