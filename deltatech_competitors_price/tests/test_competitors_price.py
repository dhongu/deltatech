# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import types
from pathlib import Path
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
        # Path to saved sample competitor page
        cls.fixture_path = Path(__file__).parent / "data" / "emag_m3100adnw.html"
        cls.fixture_html = cls.fixture_path.read_text(encoding="utf-8")
        # CEL.ro sample page fixture
        cls.cel_fixture_path = Path(__file__).parent / "data" / "cel_m3100adnw.html"
        cls.cel_fixture_html = cls.cel_fixture_path.read_text(encoding="utf-8")

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

    def test_fetch_using_saved_page_structured(self):
        # Use the saved HTML and pretend structured data parser found the lowPrice in RON
        line = self._create_line(url="https://www.emag.ro/...")
        with (
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
                lambda url, headers=None, timeout=None: _fake_response(self.fixture_html),
            ),
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.DeltatechCompetitorPrice._extract_price_from_structured_data",
                return_value=(899.90, "RON"),
            ),
        ):
            ok = line.action_fetch_price()
        self.assertTrue(ok)
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 899.90, places=2)

    def test_fetch_using_saved_page_no_extruct_fallback(self):
        # Simulate no extruct (structured parsing returns None), ensure fallback extracts meta price 999.99
        line = self._create_line(url="https://www.emag.ro/...")
        with (
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
                lambda url, headers=None, timeout=None: _fake_response(self.fixture_html),
            ),
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.DeltatechCompetitorPrice._extract_price_from_structured_data",
                return_value=(None, None),
            ),
        ):
            ok = line.action_fetch_price()
        self.assertTrue(ok)
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 999.99, places=2)

    def test_missing_url_raises(self):
        line = self._create_line(url=False)
        with self.assertRaises(UserError):
            line._do_fetch()

    # def test_network_error_sets_status(self):
    #     line = self._create_line()
    #     def _boom(url, headers=None, timeout=None):
    #         raise Exception("timeout")
    #     with patch(
    #         "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
    #         _boom,
    #     ):
    #         ok = line.action_fetch_price()
    #     self.assertFalse(ok)
    #     self.assertIn("timeout", (line.fetch_status or ""))

    def test_missing_libs_graceful(self):
        # When both requests and lxml are missing, fetch should be skipped gracefully
        line = self._create_line()
        with (
            patch("odoo.addons.deltatech_competitors_price.models.competitor_price.requests", None),
            patch("odoo.addons.deltatech_competitors_price.models.competitor_price.lxml_html", None),
        ):
            ok = line._do_fetch()
        self.assertFalse(ok)
        self.assertIn("Missing requests/lxml", (line.fetch_status or ""))

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

    def test_fetch_using_cel_page_fallback(self):
        # Use CEL.ro-like saved HTML; force structured parser to None to hit fallback
        line = self._create_line(
            url="https://www.cel.ro/multifunctional-laser-monocrom-deli-m3100adnw-31pagini-a4-adf-duplex-retea-wireless-pOSc1NDYsPw-l/"
        )
        with (
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
                lambda url, headers=None, timeout=None: _fake_response(self.cel_fixture_html),
            ),
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.DeltatechCompetitorPrice._extract_price_from_structured_data",
                return_value=(None, None),
            ),
        ):
            ok = line.action_fetch_price()
        self.assertTrue(ok)
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 1249.99, places=2)

    def test_cel_structured_via_fake_extruct(self):
        # Simulate CEL.ro page going through structured-data path by faking extruct
        line = self._create_line(
            url="https://www.cel.ro/multifunctional-laser-monocrom-deli-m3100adnw-31pagini-a4-adf-duplex-retea-wireless-pOSc1NDYsPw-l/"
        )
        # Fake extruct module with an extract() returning a JSON-LD Product + Offer
        fake_extruct = types.SimpleNamespace(
            extract=lambda html_text, syntaxes=None, base_url="": {
                "json-ld": [
                    {
                        "@context": "https://schema.org",
                        "@type": "Product",
                        "name": "Deli M3100ADNW",
                        "offers": {
                            "@type": "Offer",
                            "price": "1249,99",
                            "priceCurrency": "RON",
                        },
                    }
                ],
                "microdata": [],
            }
        )
        with (
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.requests.get",
                lambda url, headers=None, timeout=None: _fake_response(self.cel_fixture_html),
            ),
            patch(
                "odoo.addons.deltatech_competitors_price.models.competitor_price.extruct",
                fake_extruct,
            ),
        ):
            ok = line.action_fetch_price()
        self.assertTrue(ok)
        self.assertEqual(line.fetch_status, "OK")
        self.assertAlmostEqual(line.last_price or 0.0, 1249.99, places=2)
        # If RON currency exists in DB, ensure it's set
        ron = self.env["res.currency"].search([("name", "=", "RON")], limit=1)
        if ron:
            self.assertEqual(line.currency_id.id, ron.id)
