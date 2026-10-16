import json

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestCronWebhookController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_str("deltatech_cron_monitor_webhook.global_token", "global_secret")
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

    def test_status(self):
        response = self.url_open("/cron/webhook/test_webhook_ctrl/status")
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
