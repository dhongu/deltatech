# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import HttpCase, tagged

from odoo.addons.web.tests.test_js import unit_test_error_checker


@tagged("post_install", "-at_install")
class TestTaskProgressJs(HttpCase):
    """The progress dialog is tested in the browser, with the Hoot tests of static/tests."""

    def test_task_progress_dialog(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&filter=%40deltatech_task_progress",
            "",
            "",
            login="admin",
            timeout=600,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )
