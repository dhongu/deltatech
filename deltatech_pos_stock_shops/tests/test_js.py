from odoo.tests import HttpCase, tagged

from odoo.addons.web.tests.test_js import unit_test_error_checker


@tagged("post_install", "-at_install")
class TestPosStockShopsJs(HttpCase):
    """The filter, the card and the offline popup live in the browser: tested with Hoot."""

    def test_pos_stock_shops_js(self):
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&filter=%40deltatech_pos_stock_shops",
            "",
            "",
            login="admin",
            timeout=600,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )
