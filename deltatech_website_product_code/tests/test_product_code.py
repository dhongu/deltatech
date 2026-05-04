# ©  2015-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestProductCode(TransactionCase):
    def setUp(self):
        super().setUp()
        self.website = self.env.ref("website.default_website")
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "default_code": "TEST001",
                "type": "consu",
            }
        )

    def _call_search_render_results(self, product):
        fetch_fields = ["name"]
        mapping = {}
        icon = ""
        limit = 10
        with patch.object(
            type(self.env["website"]),
            "get_current_website",
            return_value=self.website,
        ):
            return product._search_render_results(fetch_fields, mapping, icon, limit)

    def test_search_render_results_with_code(self):
        """Produsul cu default_code afișează codul în nume."""
        results = self._call_search_render_results(self.product)
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
        results = self._call_search_render_results(product_no_code)
        self.assertTrue(len(results) > 0)
        self.assertNotIn("[", results[0]["name"])

    def test_search_render_results_name_format(self):
        """Formatul numelui este [COD] Nume."""
        results = self._call_search_render_results(self.product)
        self.assertTrue(results[0]["name"].startswith("[TEST001] "))
