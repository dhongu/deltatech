import json
from unittest.mock import patch

from odoo.tests import HttpCase, tagged
from odoo.tools import mute_logger

CONTROLLER_LOGGER = "odoo.addons.deltatech_cron_monitor_webhook.controllers.webhook_controller"
CRON_LOGGER = "odoo.addons.base.models.ir_cron"


@tagged("post_install", "-at_install")
class TestCronWebhookController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param("deltatech_cron_monitor_webhook.global_token", "global_secret")
        cls.cron_job = cls.env["ir.cron"].create(
            {
                "name": "Webhook Cron Job",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "model.search([], limit=1)",
                "interval_number": 1,
                "interval_type": "days",
                "user_id": cls.env.ref("base.user_admin").id,
                "enable_webhook": True,
                "webhook_code": "test_webhook_ctrl",
            }
        )
        cls.failing_cron = cls.env["ir.cron"].create(
            {
                "name": "Failing Webhook Cron Job",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "raise UserError('boom secret detail')",
                "interval_number": 1,
                "interval_type": "days",
                "user_id": cls.env.ref("base.user_admin").id,
                "enable_webhook": True,
                "webhook_code": "test_webhook_fail",
            }
        )

    def test_healthcheck(self):
        response = self.url_open("/cron/healthcheck")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, "OK")

    def test_unknown_webhook(self):
        response = self.url_open("/cron/webhook/does_not_exist?token=global_secret")
        self.assertEqual(response.status_code, 404)

    def test_invalid_token(self):
        response = self.url_open("/cron/webhook/test_webhook_ctrl?token=wrong")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.text)["status"], "error")

    def test_unknown_webhook_without_token(self):
        response = self.url_open("/cron/webhook/does_not_exist")
        self.assertEqual(response.status_code, 401)

    def test_status_without_token(self):
        response = self.url_open("/cron/webhook/test_webhook_ctrl/status")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn("Webhook Cron Job", response.text)

    def test_status_invalid_token(self):
        response = self.url_open("/cron/webhook/test_webhook_ctrl/status?token=wrong")
        self.assertEqual(response.status_code, 401)

    def test_status(self):
        response = self.url_open("/cron/webhook/test_webhook_ctrl/status?token=global_secret")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.text)
        self.assertEqual(data["job_name"], "Webhook Cron Job")

    def test_trigger_with_header_token(self):
        response = self.url_open(
            "/cron/webhook/test_webhook_ctrl",
            headers={"X-Access-Token": "global_secret"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(json.loads(response.text)["status"], "success")

    def test_trigger_success(self):
        response = self.url_open("/cron/webhook/test_webhook_ctrl?token=global_secret")
        self.assertEqual(response.status_code, 200, response.text)
        data = json.loads(response.text)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["job_name"], "Webhook Cron Job")

    @mute_logger(CONTROLLER_LOGGER)
    def test_trigger_failing_cron(self):
        # Odoo returns a display_exception action instead of raising: it must not be reported as success
        with self.assertLogs(CRON_LOGGER, level="ERROR"):
            response = self.url_open("/cron/webhook/test_webhook_fail?token=global_secret")
        self.assertEqual(response.status_code, 500, response.text)
        data = json.loads(response.text)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["job_name"], "Failing Webhook Cron Job")
        # The exception details stay in the server log
        self.assertNotIn("boom secret detail", response.text)
        self.assertNotIn("Traceback", response.text)

    @mute_logger(CONTROLLER_LOGGER)
    def test_trigger_already_running(self):
        IrCron = type(self.env["ir.cron"])
        with patch.object(IrCron, "_acquire_one_job", return_value=None):
            response = self.url_open("/cron/webhook/test_webhook_ctrl?token=global_secret")
        self.assertEqual(response.status_code, 409, response.text)
        data = json.loads(response.text)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "Job already running")
