# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests import tagged

from odoo.addons.base.tests.common import HttpCaseWithUserPortal


@tagged("post_install", "-at_install")
class TestUi(HttpCaseWithUserPortal):
    def test_01_portal_load_tour(self):
        self.start_tour("/", "portal_load_homepage", login="portal")

    def test_open_my_homepage(self):
        self.url_open("/my")
        self.url_open("/my/quotes")
        self.url_open("/my/orders")
