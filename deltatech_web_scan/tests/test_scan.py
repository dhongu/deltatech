# Part of Terrabit. See LICENSE file for full copyright and licensing details.

from types import SimpleNamespace

from odoo.tests.common import BaseCase, TransactionCase, tagged

from odoo.addons.deltatech_web_scan.utils.scan import group_by_domain, history_needs_new_interval, scan_page

from .common import PRODUCT_PAGE, FakeResponse, fake_web

URL = "https://shop.example/p/m3100"
PLAIN_PAGE = '<html><body><span id="pret">89,90 lei</span><span class="cod">XY-1</span></body></html>'


@tagged("post_install", "-at_install")
class TestScanPage(BaseCase):
    def _scan(self, page=PRODUCT_PAGE, **kwargs):
        with fake_web({URL: page}):
            return scan_page(URL, respect_robots=False, **kwargs)

    def test_ok(self):
        outcome = self._scan()
        self.assertEqual(outcome["state"], "ok")
        self.assertEqual(outcome["source"], "structured")
        self.assertEqual(outcome["offer"], {"price": 1249.5, "currency": "RON", "availability": "in_stock"})
        self.assertEqual(outcome["product"]["gtin"], "5901234123457")

    def test_same_barcode_wins_over_code(self):
        outcome = self._scan(expected={"gtin": "05901234123457", "code": "OTHER"})
        self.assertEqual(outcome["state"], "ok")

    def test_mismatch(self):
        outcome = self._scan(expected={"gtin": "96385074"})
        self.assertEqual(outcome["state"], "mismatch")
        self.assertIn("5901234123457", outcome["detail"])
        self.assertEqual(self._scan(expected={"code": "M3200"})["state"], "mismatch")
        # the code is compared without its punctuation
        self.assertEqual(self._scan(expected={"code": "m3100 adnw"})["state"], "ok")

    def test_suspect_jump(self):
        self.assertEqual(self._scan(previous_price=1200, suspect_change_percent=50)["state"], "ok")
        outcome = self._scan(previous_price=500, suspect_change_percent=50)
        self.assertEqual(outcome["state"], "suspect")
        self.assertEqual(outcome["offer"]["price"], 1249.5)

    def test_selectors_and_heuristic(self):
        selectors = [
            {"target": "price", "type": "xpath", "expression": "//span[@id='pret']"},
            {"target": "sku", "type": "xpath", "expression": "//span[@class='cod']"},
        ]
        outcome = self._scan(PLAIN_PAGE, selectors=selectors, expected={"code": "XY1"})
        self.assertEqual(outcome["state"], "ok")
        self.assertEqual(outcome["source"], "selector")
        self.assertEqual(outcome["offer"]["price"], 89.9)

        heuristic = '<body><span class="product-price">89,90 lei</span></body>'
        outcome = self._scan(heuristic)
        self.assertEqual((outcome["state"], outcome["source"]), ("ok", "heuristic"))
        self.assertEqual(self._scan(heuristic, allow_heuristic=False)["state"], "not_found")

    def test_not_found_blocked_error(self):
        self.assertEqual(self._scan("<html><body>no price</body></html>")["state"], "not_found")
        self.assertEqual(self._scan(FakeResponse("gone", status=410))["state"], "not_found")
        self.assertEqual(self._scan(FakeResponse("slow", status=429))["state"], "blocked")
        self.assertEqual(self._scan(FakeResponse("down", status=500))["state"], "error")
        with fake_web():
            self.assertEqual(scan_page("http://localhost/admin")["state"], "error")

    def test_history_interval(self):
        keys = ("price", "availability", "currency_id")
        self.assertTrue(history_needs_new_interval({}, {"price": 1.0}, keys))
        last = {"price": 10.0, "availability": "in_stock", "currency_id": 1}
        self.assertFalse(
            history_needs_new_interval(last, {"price": 10.0000001, "availability": "in_stock", "currency_id": 1}, keys)
        )
        self.assertTrue(
            history_needs_new_interval(last, {"price": 10.5, "availability": "in_stock", "currency_id": 1}, keys)
        )
        self.assertTrue(
            history_needs_new_interval(last, {"price": 10.0, "availability": "out_of_stock", "currency_id": 1}, keys)
        )

    def test_group_by_domain(self):
        items = [
            SimpleNamespace(url=u) for u in ("https://a.example/1", "https://b.example/1", "https://www.a.example/2")
        ]
        groups = group_by_domain(items, lambda i: i.url)
        self.assertEqual(list(groups), ["a.example", "b.example"])
        self.assertEqual([i.url for i in groups["a.example"]], ["https://a.example/1", "https://www.a.example/2"])


@tagged("post_install", "-at_install")
class TestScanSourceMixin(TransactionCase):
    def test_scan_fetch_keeps_state(self):
        """The mixin reads the page, keeps the state, counts the failures in a row and calls _scan_apply"""
        Source = self.env["web.scan.source.mixin"]
        record = Source.new({"scan_url": URL})
        with fake_web({URL: PRODUCT_PAGE}):
            outcomes = record._scan_fetch()
        self.assertEqual(outcomes[record.id]["state"], "ok")
        self.assertEqual(record.scan_state, "ok")
        self.assertEqual(record.scan_source, "structured")
        self.assertTrue(record.scan_last_fetch)

        failing = Source.new({"scan_url": "https://shop.example/gone", "scan_error_count": 2})
        with fake_web():
            failing._scan_fetch()
        self.assertEqual(failing.scan_state, "not_found")
        self.assertEqual(failing.scan_error_count, 3)

        no_url = Source.new({})
        no_url._scan_fetch()
        self.assertEqual(no_url.scan_state, "error")

    def test_confirm_suspect(self):
        record = self.env["web.scan.source.mixin"].new({"scan_url": URL})
        record.scan_state = "suspect"
        record.action_scan_confirm()
        self.assertEqual(record.scan_state, "ok")
