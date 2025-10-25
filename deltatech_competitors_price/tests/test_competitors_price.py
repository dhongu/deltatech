# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


def _fake_response(text, status=200):
    class Resp:
        def __init__(self, text, status):
            self.text = text
            self.status_code = status
            self.content = text.encode("utf-8")

        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP {self.status_code}")

    return Resp(text, status)


@tagged("post_install", "-at_install")
class TestDeltatechCompetitorsPrice(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env["product.template"]
        cls.product = Product.create(
            {
                "name": "Test Product",
                "list_price": 10.0,
            }
        )
        cls.Model = cls.env["deltatech.competitor.price"]

    def _create_line(self, url="http://example.com/item"):
        return self.Model.create(
            {
                "product_tmpl_id": self.product.id,
                "competitor_name": "ExampleShop",
                "product_url": url,
            }
        )

    def test_fetch_from_jsonld(self):
        # Simulate structured data extraction regardless of extruct availability
        html = "<html><head></head><body></body></html>"
        line = self._create_line()
        with (
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
                lambda url, headers=None, timeout=None: _fake_response(html),
            ),
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.DeltatechCompetitorPrice._extract_price_from_structured_data",
                return_value=(123.45, "EUR"),
            ),
        ):
            line.action_fetch_price()
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 123.45, places=3)
        # Currency may or may not exist in DB; if it exists, currency_id should be set to that
        if self.env["res.currency"].search([("name", "=", "EUR")], limit=1):
            self.assertEqual(line.currency_id.name, "EUR")

    def test_fetch_from_html_fallback(self):
        # HTML without JSON-LD, meta product price present
        html = "<html><head>" '<meta property="product:price:amount" content="987.65"/>' "</head><body></body></html>"
        line = self._create_line()
        with patch(
            "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
            lambda url, headers=None, timeout=None: _fake_response(html),
        ):
            line.action_fetch_price()
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 987.65, places=3)

    def test_missing_url_raises(self):
        line = self._create_line(url=False)
        with self.assertRaises(UserError):
            line._do_fetch()

    def test_product_template_action(self):
        # Ensure the button on product triggers on related lines
        html = "<html><head>" '<meta property="product:price:amount" content="11.11"/>' "</head><body></body></html>"
        line = self._create_line()
        with patch(
            "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
            lambda url, headers=None, timeout=None: _fake_response(html),
        ):
            self.product.action_fetch_competitor_prices()
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 11.11, places=3)
