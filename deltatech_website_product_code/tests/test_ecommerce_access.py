# ©  2015-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import json

from odoo.tests import tagged
from odoo.tests.common import HttpCase, new_test_user


@tagged("post_install", "-at_install")
class TestEcommerceAccess(HttpCase):
    """WEBCODE-001: the code search endpoints follow the "logged-in users only" shop setting."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].get_current_website()
        cls.product = cls.env["product.template"].create(
            {
                "name": "Login Gate Product",
                "default_code": "WEBCODE001GATE",
                "type": "consu",
                "is_published": True,
                "sale_ok": True,
                "list_price": 100.0,
                "website_id": cls.website.id,
            }
        )
        new_test_user(cls.env, login="webcode_portal", password="webcode_portal", groups="base.group_portal")

    def _search_http(self):
        response = self.url_open("/shop/products-search?search=WEBCODE001GATE")
        self.assertEqual(response.status_code, 200)
        return response.text

    def _search_json(self):
        response = self.url_open(
            "/shop/products-json",
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "id": 1, "params": {"search": "WEBCODE001GATE"}}),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 200)
        return response.json()["result"]

    def test_public_shop_returns_products(self):
        self.website.ecommerce_access = "everyone"
        self.assertIn("WEBCODE001GATE", self._search_http())
        self.assertEqual([p["default_code"] for p in self._search_json()], ["WEBCODE001GATE"])

    def test_login_only_shop_hides_products_from_visitors(self):
        self.website.ecommerce_access = "logged_in"
        self.assertNotIn("WEBCODE001GATE", self._search_http())
        self.assertEqual(self._search_json(), [])

    def test_login_only_shop_returns_products_to_logged_users(self):
        self.website.ecommerce_access = "logged_in"
        self.authenticate("webcode_portal", "webcode_portal")
        self.assertIn("WEBCODE001GATE", self._search_http())
        self.assertEqual([p["default_code"] for p in self._search_json()], ["WEBCODE001GATE"])

    def test_login_only_shop_product_code_link_redirects_to_login(self):
        self.website.ecommerce_access = "logged_in"
        response = self.url_open("/shop/product-code/WEBCODE001GATE", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303))
        self.assertIn("/web/login", response.headers["Location"])
        response = self.url_open("/shop/product-code/NO_SUCH_CODE_XYZ", allow_redirects=False)
        self.assertIn(response.status_code, (302, 303), "A missing code is not revealed by a 404")
