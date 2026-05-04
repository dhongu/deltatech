# ©  2015-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductCode(TransactionCase):
    def setUp(self):
        super().setUp()
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "default_code": "TEST001",
                "type": "consu",
            }
        )

    def test_search_render_results_with_code(self):
        """Produsul cu default_code afișează codul în nume."""
        fetch_fields = ["name"]
        mapping = {}
        icon = ""
        limit = 10
        results = self.product._search_render_results(fetch_fields, mapping, icon, limit)
        self.assertTrue(len(results) > 0)
        self.assertIn("[TEST001]", results[0]["name"])

    def test_search_render_results_without_code(self):
        """Produsul fără default_code nu modifică numele."""
        product_no_code = self.env["product.template"].create(
            {
                "name": "Product Without Code",
                "default_code": False,
                "type": "consu",
            }
        )
        fetch_fields = ["name"]
        mapping = {}
        icon = ""
        limit = 10
        results = product_no_code._search_render_results(fetch_fields, mapping, icon, limit)
        self.assertTrue(len(results) > 0)
        self.assertNotIn("[", results[0]["name"])

    def test_search_render_results_name_format(self):
        """Formatul numelui este [COD] Nume."""
        fetch_fields = ["name"]
        mapping = {}
        icon = ""
        limit = 10
        results = self.product._search_render_results(fetch_fields, mapping, icon, limit)
        self.assertTrue(results[0]["name"].startswith("[TEST001] "))
