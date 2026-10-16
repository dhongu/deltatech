# © 2026 Terrabit
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestNotificationSound(HttpCase):
    def _session_flag(self):
        self.authenticate("admin", "admin")
        info = self.make_jsonrpc_request("/web/session/get_session_info")
        return info["user_context"].get("notification_sound_enabled")

    def test_sounds_enabled_by_default(self):
        self.assertIs(self._session_flag(), True)

    def test_disabled_preference_reaches_the_web_client(self):
        self.env.ref("base.user_admin").notification_sound_enabled = False
        self.assertIs(self._session_flag(), False)
