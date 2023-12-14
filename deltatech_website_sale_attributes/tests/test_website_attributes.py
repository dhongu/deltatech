# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestStockWebsiteAAttribute(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        current_website = cls.env["website"].get_current_website()
        cls.current_website = current_website

    def test_call_shop(self):
        self.url_open("/shop")
