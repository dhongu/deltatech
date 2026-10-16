# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import HttpCase, tagged


@tagged("-at_install", "post_install")
class TestUi(HttpCase):
    def test_page(self):
        self.url_open("/shop?&search=cod1")
