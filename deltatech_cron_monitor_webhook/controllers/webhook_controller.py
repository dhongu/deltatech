import hashlib
import hmac
import json
import logging
import time

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CronWebhookController(http.Controller):
    def _verify_signature(self, webhook_code, timestamp, signature, secret):
        if not secret or not signature:
            return False
        expected = hmac.new(secret.encode(), f"{webhook_code}{timestamp}".encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def _make_json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, default=str), headers=[("Content-Type", "application/json")], status=status
        )

    @http.route("/cron/webhook/<string:webhook_code>", type="http", auth="none", methods=["POST"], csrf=False)
    def trigger_cron(self, webhook_code, **kw):
        # We need to use sudo() and a proper environment since auth is none
        cron = (
            request.env["ir.cron"]
            .sudo()
            .search([("webhook_code", "=", webhook_code), ("enable_webhook", "=", True)], limit=1)
        )

        if not cron:
            return self._make_json_response(
                {"status": "error", "message": "Invalid webhook code or disabled"}, status=404
            )

        # JSON data for type='http' needs to be parsed manually if sent as application/json
        try:
            params = json.loads(request.httprequest.data) if request.httprequest.data else {}
        except Exception:
            params = {}

        # Verify signature if enabled
        verify = (
            request.env["ir.config_parameter"]
            .sudo()
            .get_param("deltatech_cron_monitor_webhook.verify_signature", "False")
            == "True"
        )
        if verify:
            signature = request.httprequest.headers.get("X-Signature")
            timestamp = params.get("timestamp", "")
            secret = request.env["ir.config_parameter"].sudo().get_param("deltatech_cron_monitor_webhook.master_secret")
            if not self._verify_signature(webhook_code, timestamp, signature, secret):
                return self._make_json_response({"status": "error", "message": "Invalid signature"}, status=401)

        start_time = time.time()
        try:
            # Execute the cron job
            cron.with_context(cron_trigger_type="webhook").method_direct_trigger()
            duration = time.time() - start_time

            return self._make_json_response(
                {
                    "status": "success",
                    "job_name": cron.name,
                    "execution_time": duration,
                    "timestamp": fields.Datetime.now(),
                }
            )
        except Exception as e:
            duration = time.time() - start_time
            _logger.error("Webhook execution failed for %s: %s", webhook_code, str(e))
            return self._make_json_response({"status": "error", "message": str(e)}, status=500)

    @http.route("/cron/webhook/<string:webhook_code>/status", type="http", auth="none", methods=["GET"])
    def get_status(self, webhook_code, **kw):
        cron = (
            request.env["ir.cron"]
            .sudo()
            .search([("webhook_code", "=", webhook_code), ("enable_webhook", "=", True)], limit=1)
        )

        if not cron:
            return self._make_json_response(
                {"status": "error", "message": "Invalid webhook code or disabled"}, status=404
            )

        return self._make_json_response(
            {"status": "ok", "job_name": cron.name, "next_run": cron.nextcall, "active": cron.active}
        )

    @http.route("/cron/healthcheck", type="http", auth="none", methods=["GET"])
    def healthcheck(self, **kw):
        return "OK"
