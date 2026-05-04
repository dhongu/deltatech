# ©  2015-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged("post_install", "-at_install")
class TestWebsiteProductCode(HttpCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product Code",
                "default_code": "WEBTEST001",
                "type": "consu",
                "is_published": True,
            }
        )

    def test_product_by_code_found(self):
        """Ruta /shop/product-code/<code> returnează pagina produsului."""
        response = self.url_open("/shop/product-code/WEBTEST001")
        self.assertEqual(response.status_code, 200)

    def test_product_by_code_not_found(self):
        """Ruta /shop/product-code/<code> returnează 404 pentru cod inexistent."""
        response = self.url_open("/shop/product-code/NONEXISTENT_CODE_XYZ")
        self.assertEqual(response.status_code, 404)

    def test_products_search_by_code(self):
        """Ruta /shop/products-search returnează rezultate pentru căutare după cod."""
        response = self.url_open("/shop/products-search?search=WEBTEST001")
        self.assertEqual(response.status_code, 200)

    def test_products_search_empty(self):
        """Ruta /shop/products-search fără parametri returnează răspuns valid."""
        response = self.url_open("/shop/products-search")
        self.assertEqual(response.status_code, 200)
