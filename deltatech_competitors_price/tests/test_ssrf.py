# © 2026 Deltatech / Terrabit
# Regression tests for COMPETITOR-001 (SSRF on price fetch)
from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

MODULE = "odoo.addons.deltatech_competitors_price.models.competitor_price"

HTML = '<html><head><meta property="product:price:amount" content="12.50"/></head><body></body></html>'


class _Resp:
    def __init__(self, text="", status=200, location=None):
        self.text = text
        self.content = text.encode("utf-8")
        self.status_code = status
        self.headers = {"location": location} if location else {}
        self.is_redirect = bool(location)

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def _fake_dns(host, port):
    return {
        "shop.example": {"93.184.215.14"},
        "localhost": {"127.0.0.1"},
        "internal.example": {"10.1.2.3"},
        "mixed.example": {"93.184.215.14", "192.168.1.10"},
        "metadata.example": {"169.254.169.254"},
        "v6local.example": {"::1"},
        "mapped.example": {"::ffff:127.0.0.1"},
    }[host]


@tagged("post_install", "-at_install")
class TestCompetitorPriceSsrf(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.template"].create({"name": "SSRF product"})

    def setUp(self):
        super().setUp()
        patcher = patch(f"{MODULE}._resolve_host_ips", side_effect=_fake_dns)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _line(self, url):
        return self.env["deltatech.competitor.price"].create(
            {"product_tmpl_id": self.product.id, "competitor_name": "Shop", "product_url": url}
        )

    def _fetch(self, url, responses=None):
        line = self._line(url)
        calls = []

        def _get(u, **kw):
            calls.append(u)
            return (responses or {}).get(u) or _Resp(HTML)

        with patch(f"{MODULE}.requests.get", side_effect=_get):
            ok = line.action_fetch_price()
        return line, ok, calls

    def test_private_destinations_are_not_requested(self):
        for url in (
            "http://127.0.0.1:8069/",
            "http://localhost:8069/web",
            "http://10.0.0.5/",
            "http://192.168.1.1/admin",
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]:8069/",
            "http://internal.example/",
            "http://mixed.example/",
            "http://metadata.example/",
            "http://v6local.example/",
            "http://mapped.example/",
            "file:///etc/passwd",
            "ftp://shop.example/x",
        ):
            line, ok, calls = self._fetch(url)
            self.assertFalse(ok, url)
            self.assertEqual(calls, [], url)
            self.assertFalse(line.last_price, url)
            self.assertRegex(line.fetch_status, "non-public|http\\(s\\)", url)

    def test_redirect_to_private_host_is_not_followed(self):
        url = "https://shop.example/p/1"
        line, ok, calls = self._fetch(
            url, responses={url: _Resp(status=302, location="http://127.0.0.1:8069/web/database/manager")}
        )
        self.assertFalse(ok)
        self.assertEqual(calls, [url])
        self.assertIn("non-public", line.fetch_status)

    def test_public_url_and_public_redirect_still_work(self):
        url = "https://shop.example/p/1"
        line, ok, calls = self._fetch(url, responses={url: _Resp(status=301, location="/p/1-new")})
        self.assertTrue(ok)
        self.assertEqual(calls, [url, "https://shop.example/p/1-new"])
        self.assertEqual(line.last_price, 12.5)

    def test_redirect_loop_is_bounded(self):
        url = "https://shop.example/loop"
        line, ok, calls = self._fetch(url, responses={url: _Resp(status=302, location=url)})
        self.assertFalse(ok)
        self.assertLessEqual(len(calls), 6)
