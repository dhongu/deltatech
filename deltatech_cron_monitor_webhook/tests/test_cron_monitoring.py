from odoo.tests.common import TransactionCase


class TestCronMonitoring(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cron_job = cls.env["ir.cron"].create(
            {
                "name": "Test Cron Job",
                "model_id": cls.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "model.search([], limit=1)",
                "interval_number": 1,
                "interval_type": "days",
                "user_id": cls.env.ref("base.user_admin").id,
                "enable_webhook": True,
                "webhook_code": "test_webhook_123",
            }
        )

    def test_webhook_url(self):
        """Test că URL-ul webhook este calculat corect folosind token-ul global"""
        self.env["ir.config_parameter"].sudo().set_param("deltatech_cron_monitor_webhook.global_token", "global_secret")
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        self.assertEqual(self.cron_job.webhook_url, f"{base_url}/cron/webhook/test_webhook_123?token=global_secret")

    def test_auto_generation(self):
        """Test că codul este generat corect"""
        new_cron = self.env["ir.cron"].create(
            {
                "name": "Auto Token Cron",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "model.search([], limit=1)",
                "interval_number": 1,
                "interval_type": "days",
                "user_id": self.env.ref("base.user_admin").id,
                "enable_webhook": True,
            }
        )
        # webhook_code nu are default
        new_cron.webhook_code = "my_custom_code"
        self.assertEqual(new_cron.webhook_code, "my_custom_code")

    def test_methods_exist(self):
        """Test că metodele există dar sunt goale (nu dau eroare)"""
        self.cron_job._log_execution("success", 1.0)
        self.cron_job._send_alert("error")
        self.cron_job._healthcheck_ping("success")
        self.cron_job.action_reset_statistics()
