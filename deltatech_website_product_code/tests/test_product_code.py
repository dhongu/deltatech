# ©  2015-2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.website_sale.tests.common import MockRequest


@tagged("post_install", "-at_install")
class TestProductCode(TransactionCase):
    def setUp(self):
        super().setUp()
        self.website = self.env.ref("base.default_website")
        self.product = self.env["product.template"].create(
            {
                "name": "Test Product",
                "default_code": "TEST001",
                "type": "consu",
            }
        )

    def _call_search_render_results(self, product):
        fetch_fields = ["name"]
        # 20.0 renders the price from the mapping of the search detail
        mapping = {"search_item_metadata": {"display_currency": self.website.currency_id}}
        icon = ""
        limit = 10
        # website.get_current_website() is gone in 20.0: the current website is env.website, and
        # website_sale reads the pricelist of the combination info from the request
        env = self.env(context=dict(self.env.context, website_id=self.website.id))
        with MockRequest(env, website=self.website.with_env(env)):
            return product.with_env(env)._search_render_results(fetch_fields, mapping, icon, limit)

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
