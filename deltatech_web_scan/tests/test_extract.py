# Part of Terrabit. See LICENSE file for full copyright and licensing details.

from odoo.tests.common import BaseCase, tagged

from odoo.addons.deltatech_web_scan.utils.codes import (
    is_valid_gtin,
    normalize_code,
    normalize_gtin,
    parse_price,
    same_code,
    same_gtin,
)
from odoo.addons.deltatech_web_scan.utils.extract import (
    best_offer,
    extract_by_selectors,
    extract_images,
    extract_price_heuristic,
    extract_structured,
    page_text,
)

from .common import PRODUCT_PAGE

URL = "https://shop.example/p/m3100"


@tagged("post_install", "-at_install")
class TestCodes(BaseCase):
    def test_parse_price(self):
        cases = {
            "1.299,00 lei": 1299.0,
            "1,299.00": 1299.0,
            "1299 lei": 1299.0,
            "1 299,99": 1299.99,
            "1 299,99 RON": 1299.99,
            "12.50": 12.5,
            "0,99 RON": 0.99,
            "1.299": 1299.0,
            "1,299": 1299.0,
            "1.299.000": 1299000.0,
            "Price: 45,5 EUR": 45.5,
            "free": None,
            "": None,
            None: None,
            True: None,
            -3: None,
            19.9: 19.9,
        }
        for value, expected in cases.items():
            self.assertEqual(parse_price(value), expected, repr(value))

    def test_parse_price_structured(self):
        """schema.org uses a dot as decimal separator; a Romanian price is still read right"""
        self.assertEqual(parse_price("1.299", structured=True), 1.299)
        self.assertEqual(parse_price("1.299,00", structured=True), 1299.0)
        self.assertEqual(parse_price("1299.90", structured=True), 1299.9)

    def test_codes(self):
        self.assertEqual(normalize_code(" ab-12/3.x_y "), "AB123XY")
        self.assertEqual(normalize_code("00123", strip_zeros=True), "123")
        self.assertTrue(same_code("M3100-ADNW", "m3100adnw"))
        self.assertFalse(same_code("00123", "123"))
        self.assertTrue(same_code("00123", "123", strip_zeros=True))
        self.assertFalse(same_code("", ""))

    def test_gtin(self):
        self.assertEqual(normalize_gtin("590 1234-123457"), "5901234123457")
        self.assertEqual(normalize_gtin("ABC123"), "")
        self.assertTrue(is_valid_gtin("5901234123457"))
        self.assertFalse(is_valid_gtin("5901234123458"))
        self.assertTrue(is_valid_gtin("96385074"))  # GTIN-8
        self.assertTrue(same_gtin("05901234123457", "5901234123457"))
        self.assertFalse(same_gtin("", ""))


@tagged("post_install", "-at_install")
class TestExtract(BaseCase):
    def test_json_ld_product(self):
        products = extract_structured(PRODUCT_PAGE, URL)
        self.assertEqual(len(products), 1)
        product = products[0]
        self.assertEqual(product["name"], "Printer M3100")
        self.assertEqual(product["brand"], "Samsung")
        self.assertEqual(product["sku"], "M3100-ADNW")
        self.assertEqual(product["gtin"], "5901234123457")
        self.assertEqual(product["images"], ["https://shop.example/img/m3100.jpg", "https://cdn.example/m3100-2.jpg"])
        self.assertEqual(
            product["offers"],
            [
                {"price": 1199.0, "currency": "RON", "availability": "out_of_stock"},
                {"price": 1249.5, "currency": "RON", "availability": "in_stock"},
            ],
        )
        # the cheapest offer in stock, not the cheapest one
        self.assertEqual(best_offer(product)["price"], 1249.5)
        self.assertEqual(best_offer(product, prefer_in_stock=False)["price"], 1199.0)

    def test_microdata_and_aggregate_offer(self):
        microdata = """<div itemscope itemtype="http://schema.org/Product"><span itemprop="name">Rotor</span>
            <span itemprop="sku">R-1</span>
            <div itemprop="offers" itemscope itemtype="http://schema.org/Offer"><meta itemprop="price" content="45.50">
            <meta itemprop="priceCurrency" content="EUR"><link itemprop="availability" href="http://schema.org/InStock">
            </div></div>"""
        product = extract_structured(microdata, URL)[0]
        self.assertEqual(product["sku"], "R-1")
        self.assertEqual(product["offers"], [{"price": 45.5, "currency": "EUR", "availability": "in_stock"}])

        aggregate = """<script type="application/ld+json">{"@type": "Product", "name": "Kit",
            "offers": {"@type": "AggregateOffer", "lowPrice": "19.90", "highPrice": "29.90", "priceCurrency": "EUR"}}
            </script>"""
        self.assertEqual(extract_structured(aggregate, URL)[0]["offers"][0]["price"], 19.9)

    def test_broken_and_empty_pages(self):
        self.assertEqual(extract_structured("", URL), [])
        self.assertEqual(extract_structured("<script type='application/ld+json'>{broken</script>", URL), [])
        self.assertEqual(extract_images("", URL), [])
        self.assertIsNone(extract_price_heuristic(""))

    def test_images(self):
        self.assertEqual(
            extract_images(PRODUCT_PAGE, URL),
            [
                "https://shop.example/img/m3100.jpg",
                "https://cdn.example/m3100-2.jpg",
                "https://shop.example/og.jpg",
            ],
        )

    def test_selectors(self):
        page = """<html><body><span class="sku">COD: AB-12</span><span id="pret">1.249,99 lei</span>
            <span id="stoc">Disponibil: În stoc</span><img class="main" src="/i/1.jpg"/>
            <script>var productId = 4711;</script>
            <script type="application/ld+json">{"@type": "Product", "offers": [{"price": "10"}, {"price": "12"}]}</script>
            </body></html>"""
        selectors = [
            {"target": "price", "type": "xpath", "expression": "//span[@id='missing']"},
            {"target": "price", "type": "xpath", "expression": "//span[@id='pret']"},
            {"target": "availability", "type": "xpath", "expression": "//span[@id='stoc']",
             "value_map": {"în stoc": "in_stock", "la comandă": "preorder"}},
            {"target": "image", "type": "xpath", "expression": "//img[@class='main']", "attribute": "src"},
            {"target": "code", "type": "regex", "expression": r"productId = (\d+)"},
            {"target": "second", "type": "jsonld_path", "expression": "offers.1.price"},
            {"target": "broken", "type": "xpath", "expression": "//span["},
        ]  # fmt: skip
        self.assertEqual(
            extract_by_selectors(page, selectors, URL),
            {
                "price": "1.249,99 lei",
                "availability": "in_stock",
                "image": "https://shop.example/i/1.jpg",
                "code": "4711",
                "second": "12",
            },
        )

    def test_heuristic_price_leaves_old_price_out(self):
        page = """<body><div class="price"><del>1.500 lei</del></div><span class="old-price">1.600 lei</span>
            <div class="price-box"><span class="price-old">1.700</span> <span class="product-price">1.249,99 lei</span></div>
            </body>"""
        self.assertEqual(extract_price_heuristic(page), 1249.99)
        meta = '<head><meta property="product:price:amount" content="99.90"/></head>'
        self.assertEqual(extract_price_heuristic(meta), 99.9)

    def test_page_text(self):
        page = "<body><h1>Title</h1><script>var x = 1;</script><style>p{}</style><!-- hidden --><p>Text <b>bold</b></p></body>"
        self.assertEqual(page_text(page), "Title Text bold")
        self.assertEqual(page_text(page, limit=5), "Title")
