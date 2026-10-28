# Part of Terrabit. See LICENSE file for full copyright and licensing details.

from unittest.mock import MagicMock, patch

from odoo.tests.common import BaseCase, tagged

from odoo.addons.deltatech_web_scan.utils import fetch as web_fetch

from .common import FETCH, FakeResponse, fake_dns, fake_web

PAGE = "<html><body>product</body></html>"


@tagged("post_install", "-at_install")
class TestPublicUrl(BaseCase):
    def test_public_and_private_hosts(self):
        with patch(f"{FETCH}._resolve_host_ips", side_effect=fake_dns):
            self.assertTrue(web_fetch.is_public_url("https://shop.example/p/1"))
            for url in (
                "http://localhost/",
                "http://127.0.0.1:8069/web",
                "http://internal.example/",
                "http://mixed.example/",
                "http://metadata.example/latest/meta-data/",
                "http://v6local.example/",
                "http://mapped.example/",
                "http://[::1]/",
                "ftp://shop.example/file",
                "file:///etc/passwd",
                "https://unknown.example/",
                "not an url",
            ):
                self.assertFalse(web_fetch.is_public_url(url), url)

    def test_socket_reaching_private_address_is_closed(self):
        """A DNS answer changed after the check (DNS rebinding) is caught when the socket opens"""

        class Base:
            host = "shop.example"

            def _new_conn(self):
                return sock

        class Connection(web_fetch._PublicPeerMixin, Base):
            pass

        sock = MagicMock()
        sock.getpeername.return_value = ("10.0.0.5", 443)
        with self.assertRaises(web_fetch.UnsafeUrl):
            Connection()._new_conn()
        sock.close.assert_called_once()

        sock = MagicMock()
        sock.getpeername.return_value = ("93.184.215.14", 443)
        self.assertIs(Connection()._new_conn(), sock)

    def test_session_does_not_use_environment_proxies(self):
        session = web_fetch.new_session("TestAgent/1.0")
        self.assertFalse(session.trust_env)
        self.assertEqual(session.headers["User-Agent"], "TestAgent/1.0")
        self.assertIsInstance(session.get_adapter("https://shop.example/"), web_fetch.PublicOnlyAdapter)


@tagged("post_install", "-at_install")
class TestFetch(BaseCase):
    def test_read_page(self):
        with fake_web({"https://shop.example/p/1": PAGE}) as calls:
            result = web_fetch.fetch("https://shop.example/p/1")
        self.assertTrue(result.ok)
        self.assertEqual(result.text, PAGE)
        self.assertEqual(calls, ["https://shop.example/robots.txt", "https://shop.example/p/1"])

    def test_private_address_is_never_requested(self):
        with fake_web() as calls:
            result = web_fetch.fetch("http://internal.example/admin")
        self.assertEqual(result.state, "refused")
        self.assertEqual(calls, [])

    def test_redirect_to_private_host_is_not_followed(self):
        pages = {"https://shop.example/p/1": FakeResponse(status=302, location="http://localhost:8069/web")}
        with fake_web(pages) as calls:
            result = web_fetch.fetch("https://shop.example/p/1", respect_robots=False)
        self.assertEqual(result.state, "refused")
        self.assertNotIn("http://localhost:8069/web", calls)

    def test_public_redirect_is_followed_and_loop_is_bounded(self):
        pages = {
            "https://shop.example/old": FakeResponse(status=301, location="/new"),
            "https://shop.example/new": PAGE,
            "https://shop.example/loop": FakeResponse(status=302, location="/loop"),
        }
        with fake_web(pages) as calls:
            result = web_fetch.fetch("https://shop.example/old", respect_robots=False)
            self.assertTrue(result.ok)
            self.assertEqual(result.url, "https://shop.example/new")
            loop = web_fetch.fetch("https://shop.example/loop", respect_robots=False)
        self.assertEqual(loop.state, "error")
        self.assertEqual(calls.count("https://shop.example/loop"), web_fetch.MAX_REDIRECTS + 1)

    def test_size_limit_and_content_type(self):
        pages = {
            "https://shop.example/big": "x" * 5000,
            "https://shop.example/file.pdf": FakeResponse("%PDF", content_type="application/pdf"),
        }
        with fake_web(pages):
            big = web_fetch.fetch("https://shop.example/big", respect_robots=False, max_size=1000)
            pdf = web_fetch.fetch("https://shop.example/file.pdf", respect_robots=False)
            any_type = web_fetch.fetch("https://shop.example/file.pdf", respect_robots=False, accept=None)
        self.assertEqual(len(big.content), 1000)
        self.assertEqual(pdf.state, "error")
        self.assertTrue(any_type.ok)

    def test_not_found_and_errors(self):
        pages = {"https://shop.example/down": FakeResponse("oops", status=500)}
        with fake_web(pages):
            self.assertEqual(web_fetch.fetch("https://shop.example/gone", respect_robots=False).state, "not_found")
            self.assertEqual(web_fetch.fetch("https://shop.example/down", respect_robots=False).state, "error")

    def test_robots_txt(self):
        robots = {"https://shop.example": "User-agent: *\nDisallow: /private/\n"}
        pages = {"https://shop.example/private/p": PAGE, "https://shop.example/p": PAGE}
        with fake_web(pages, robots) as calls:
            refused = web_fetch.fetch("https://shop.example/private/p")
            allowed = web_fetch.fetch("https://shop.example/p")
            ignored = web_fetch.fetch("https://shop.example/private/p", respect_robots=False)
        self.assertEqual(refused.state, "blocked")
        self.assertTrue(allowed.ok)
        self.assertTrue(ignored.ok)
        # robots.txt is read once, and the forbidden page only when robots.txt is ignored
        self.assertEqual(calls.count("https://shop.example/robots.txt"), 1)
        self.assertEqual(calls.count("https://shop.example/private/p"), 1)

    def test_antibot_page_is_blocked(self):
        pages = {
            "https://shop.example/limit": FakeResponse("slow down", status=429),
            "https://shop.example/forbidden": FakeResponse("<html><body>Access denied</body></html>", status=403),
            "https://shop.example/challenge": (
                "<html><head><title>Just a moment...</title></head><body>"
                "<script>window._cf_chl_opt = {cvId: '3'};</script>"
                '<script src="/cdn-cgi/challenge-platform/h/b/orchestrate/chl_page/v1?ray=x"></script></body></html>'
            ),
            "https://shop.example/datadome": '<html><script src="https://geo.captcha-delivery.com/captcha/"></script></html>',
        }
        with fake_web(pages):
            for url in pages:
                self.assertEqual(web_fetch.fetch(url, respect_robots=False).state, "blocked", url)

    def test_normal_page_with_protection_script_is_read(self):
        """Cloudflare adds its detection script to every page, and a page may have a CAPTCHA in a form:
        the page is still the one asked for (a site such as granit-parts.ro was reported as blocked)"""
        pages = {
            "https://shop.example/p/1": (
                "<html><head><title>Rulment 6204</title></head><body><h1>Rulment 6204</h1>"
                "<script>(function(){var a=document.createElement('script');"
                "a.src='/cdn-cgi/challenge-platform/scripts/jsd/main.js';"
                "document.head.appendChild(a);})();</script></body></html>"
            ),
            "https://shop.example/p/2": (
                '<html><body><h1>Product</h1><form action="/login"><input name="password"/>'
                '<div class="g-recaptcha" data-sitekey="x"></div>'
                '<script src="https://www.google.com/recaptcha/api.js"></script></form></body></html>'
            ),
            "https://shop.example/p/3": (
                '<html><body><form><div class="cf-turnstile" data-sitekey="x"></div></form>'
                '<script src="https://challenges.cloudflare.com/turnstile/v0/api.js"></script></body></html>'
            ),
        }
        with fake_web(pages):
            for url in pages:
                self.assertEqual(web_fetch.fetch(url, respect_robots=False).state, "ok", url)

    def test_pause_between_requests_to_same_domain(self):
        pages = {"https://shop.example/a": PAGE, "https://shop.example/b": PAGE, "https://other.example/c": PAGE}
        with fake_web(pages):
            with patch(f"{FETCH}.time.monotonic", return_value=1000.0), patch(f"{FETCH}.time.sleep") as sleep:
                web_fetch.fetch("https://shop.example/a", respect_robots=False, delay=3)
                web_fetch.fetch("https://other.example/c", respect_robots=False, delay=3)
                self.assertFalse(sleep.called)
                web_fetch.fetch("https://shop.example/b", respect_robots=False, delay=3)
                sleep.assert_called_once_with(3.0)

    def test_domains(self):
        self.assertEqual(web_fetch.domain_of("https://WWW.Shop.example:443/p"), "shop.example")
        self.assertTrue(web_fetch.is_excluded("https://img.pinterest.com/x", ["pinterest.com"]))
        self.assertFalse(web_fetch.is_excluded("https://notpinterest.com/x", ["pinterest.com"]))
