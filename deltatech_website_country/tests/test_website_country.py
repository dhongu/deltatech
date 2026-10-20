# ©  2008-2026 Terrabit
# See README.rst file on addons root folder for license details

import lxml.html

from odoo.tests import HttpCase, new_test_user, tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteCountry(HttpCase, WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.country_ro = cls.env.ref("base.ro")
        cls.website.company_id.country_id = cls.country_ro
        cls.portal_user = new_test_user(
            cls.env, login="dt_country_portal", groups="base.group_portal", name="Portal Country"
        )
        cls.portal_user.partner_id.country_id = False

    def _selected_country(self, response):
        self.assertEqual(response.status_code, 200)
        root = lxml.html.fromstring(response.content)
        selected = root.xpath('//select[@id="o_country_id"]/option[@selected]/@value')
        return selected and int(selected[0])

    def test_public_visitor_address_form(self):
        """The anonymous checkout preselects the country of the website's company."""
        self.make_jsonrpc_request(
            "/shop/cart/add",
            {"product_template_id": self.product.product_tmpl_id.id, "product_id": self.product.id, "quantity": 1},
        )
        response = self.url_open("/shop/address")
        self.assertEqual(self._selected_country(response), self.country_ro.id)

    def test_portal_user_address_form(self):
        """A customer without a country gets the company's country on the address form."""
        self._create_so(partner_id=self.portal_user.partner_id.id)
        self.authenticate(self.portal_user.login, self.portal_user.login)
        response = self.url_open("/shop/address")
        self.assertEqual(self._selected_country(response), self.country_ro.id)
