# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged

from odoo.addons.web.tests.test_js import unit_test_error_checker


@tagged("post_install", "-at_install")
class TestFontAwesomeJs(HttpCase):
    """The widget lives in the browser: tested with Hoot, including the unset field case (#3511)."""

    def test_fontawesome_widget(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&filter=deltatech_widget_fontawesome",
            "",
            "",
            login="admin",
            timeout=600,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )
