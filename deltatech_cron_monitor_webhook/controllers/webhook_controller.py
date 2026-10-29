import hmac
import json
import logging
import time

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class CronWebhookController(http.Controller):
    def _make_json_response(self, data, status=200):
        return request.make_response(
            json.dumps(data, default=str), headers=[("Content-Type", "application/json")], status=status
        )

    def _check_token(self, **kw):
        token = kw.get("token") or request.httprequest.headers.get("X-Access-Token")
        if (
            not token
            and request.httprequest.method == "POST"
            and request.httprequest.content_type == "application/json"
        ):
            try:
                data = json.loads(request.httprequest.data)
                token = data.get("token")
            except (ValueError, TypeError):
                _logger.debug("Failed to parse JSON body for token extraction")

        global_token = (
            request.env["ir.config_parameter"].sudo().get_param("deltatech_cron_monitor_webhook.global_token")
        )
        return bool(global_token and token and hmac.compare_digest(global_token, token))

    def _get_cron(self, webhook_code):
        # We need to use sudo() and a proper environment since auth is none
        return (
            request.env["ir.cron"]
            .sudo()
            .search([("webhook_code", "=", webhook_code), ("enable_webhook", "=", True)], limit=1)
        )

    @http.route(
        "/cron/webhook/<string:webhook_code>",
        type="http",
        auth="none",
        methods=["POST", "GET"],
        csrf=False,
        readonly=False,
    )
    def trigger_cron(self, webhook_code, **kw):
        # Check the token first, so an unknown code cannot be told apart from a wrong token
        if not self._check_token(**kw):
            return self._make_json_response({"status": "error", "message": "Invalid token"}, status=401)

        cron = self._get_cron(webhook_code)
        if not cron:
            return self._make_json_response(
                {"status": "error", "message": "Invalid webhook code or disabled"}, status=404
            )

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
        if not self._check_token(**kw):
            return self._make_json_response({"status": "error", "message": "Invalid token"}, status=401)

        cron = self._get_cron(webhook_code)
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
