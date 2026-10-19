# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged

from odoo.addons.web.tests.test_js import unit_test_error_checker


@tagged("post_install", "-at_install")
class TestListViewJs(HttpCase):
    """The x2many list lives in the browser: tested with Hoot."""

    def test_static_list_delete(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&filter=deltatech_list_view",
            "",
            "",
            login="admin",
            timeout=600,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )
