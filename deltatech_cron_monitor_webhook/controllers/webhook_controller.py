import hmac
import json
import logging
import time

from odoo import fields, http
from odoo.exceptions import UserError
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
            # Since Odoo 19 a failing job does not raise: the failure comes back as a
            # client action (tag ``display_exception``), and ``True`` means success
            result = cron.with_context(cron_trigger_type="webhook").method_direct_trigger()
        except UserError:
            # The only UserError raised by method_direct_trigger: the job is already running
            _logger.warning("Webhook trigger refused for %s: job already running", webhook_code)
            return self._make_json_response(
                self._result_payload(cron, start_time, "error", message="Job already running"), status=409
            )
        except Exception:
            _logger.exception("Webhook execution failed for %s", webhook_code)
            return self._make_json_response(
                self._result_payload(cron, start_time, "error", message="Cron execution failed"), status=500
            )

        if isinstance(result, dict) and result.get("tag") == "display_exception":
            # The traceback is already in the server log; do not expose it to the caller
            _logger.error("Webhook execution failed for %s: the cron job raised an exception", webhook_code)
            return self._make_json_response(
                self._result_payload(cron, start_time, "error", message="Cron execution failed"), status=500
            )

        return self._make_json_response(self._result_payload(cron, start_time, "success"))

    def _result_payload(self, cron, start_time, status, message=None):
        payload = {
            "status": status,
            "job_name": cron.name,
            "execution_time": time.time() - start_time,
            "timestamp": fields.Datetime.now(),
        }
        if message:
            payload["message"] = message
        return payload

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
