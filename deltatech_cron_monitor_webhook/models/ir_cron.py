import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrCron(models.Model):
    _inherit = "ir.cron"

    # Webhook Integration
    enable_webhook = fields.Boolean("Enable Webhook", copy=False)
    webhook_code = fields.Char("Webhook Code", copy=False)
    _sql_constraints = [("webhook_code_unique", "unique(webhook_code)", "Webhook Code must be unique!")]
    webhook_url = fields.Char("Webhook URL", compute="_compute_webhook_url")

    @api.depends("webhook_code")
    def _compute_webhook_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for cron in self:
            if cron.webhook_code:
                cron.webhook_url = f"{base_url}/cron/webhook/{cron.webhook_code}"
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
