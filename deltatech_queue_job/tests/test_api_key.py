# © 2026 Deltatech / Terrabit
# Regression tests for QUEUE-002 (shipped shared API key)
from odoo.tests import HttpCase, tagged

PLACEHOLDER = "sk_live_CHANGE_ME_generate_random_key_here_123456789"
KEY_PARAM = "queue_job_processor.api_key"


@tagged("post_install", "-at_install")
class TestQueueApiKey(HttpCase):
    def _set_key(self, value):
        self.env["ir.config_parameter"].sudo().set_param(KEY_PARAM, value)

    def _call(self, route, api_key):
        return self.make_jsonrpc_request(route, {"api_key": api_key})

    def _assert_denied(self, api_key):
        for route in ("/api/v1/queue/process", "/api/v1/queue/stats"):
            result = self._call(route, api_key)
            self.assertEqual(result["result"]["status"], "error", f"{route} accepted {api_key!r}")
            self.assertNotIn("stats", result["result"])
            self.assertNotIn("processed", result["result"])

    def test_install_ships_no_shared_key(self):
        self.assertNotEqual(self.env["ir.config_parameter"].sudo().get_param(KEY_PARAM), PLACEHOLDER)

    def test_placeholder_key_is_rejected(self):
        # an existing installation that kept the placeholder must not authenticate with it
        self._set_key(PLACEHOLDER)
        self._assert_denied(PLACEHOLDER)

    def test_empty_configuration_disables_api(self):
        self._set_key(False)
        self._assert_denied("")
        self._assert_denied(None)
        self._assert_denied(PLACEHOLDER)

    def test_wrong_key_is_rejected(self):
        self._set_key("a-unique-generated-key-1234567890")
        self._assert_denied("another-key")
        self._assert_denied(None)

    def test_generated_key_authenticates(self):
        settings = self.env["res.config.settings"].create({})
        settings.action_generate_queue_job_processor_api_key()
        settings.execute()
        key = self.env["ir.config_parameter"].sudo().get_param(KEY_PARAM)
        self.assertTrue(key)
        self.assertNotEqual(key, PLACEHOLDER)
        stats = self._call("/api/v1/queue/stats", key)["result"]
        self.assertEqual(stats["status"], "success")
        self.assertIn("pending", stats["stats"])
        process = self._call("/api/v1/queue/process", key)["result"]
        self.assertEqual(process["status"], "success")
