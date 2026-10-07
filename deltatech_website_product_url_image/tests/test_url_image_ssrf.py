# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, new_test_user, tagged

from .test_product_url_image import GETADDRINFO, PUBLIC_IP, REQUESTS_GET, URL, _addrinfo, _png_bytes, _response


@tagged("post_install", "-at_install")
class TestUrlImageSsrf(TransactionCase):
    """URLIMAGE-002: the server must not fetch non-public URLs (SSRF)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.png = _png_bytes()
        cls.template = cls.env["product.template"].create({"name": "SSRF Product", "type": "consu"})

    def _load(self, url, ips=(PUBLIC_IP,), responses=None):
        responses = responses or [_response(self.png)]
        with (
            patch(GETADDRINFO, return_value=_addrinfo(*ips)) as mock_dns,
            patch(REQUESTS_GET, side_effect=responses) as mock_get,
        ):
            data = self.template._load_image_from_url(url)
        return data, mock_get, mock_dns

    def test_public_url_accepted(self):
        data, mock_get, _dns = self._load(URL)
        self.assertEqual(data, base64.b64encode(self.png))
        mock_get.assert_called_once_with(URL, timeout=15, stream=True, allow_redirects=False)

    def test_literal_non_public_ips_refused(self):
        for url in (
            "http://127.0.0.1/a.png",
            "http://localhost.:8069/a.png",
            "http://[::1]/a.png",
            "http://10.0.0.5/a.png",
            "http://192.168.1.10/a.png",
            "http://172.16.0.1/a.png",
            "http://169.254.169.254/latest/meta-data/",
            "http://[fd00::1]/a.png",
            "http://[fe80::1]/a.png",
            "http://[::ffff:127.0.0.1]/a.png",
            "http://224.0.0.1/a.png",
            "http://0.0.0.0/a.png",
        ):
            with self.subTest(url=url):
                data, mock_get, _dns = self._load(url, ips=("127.0.0.1",))
                self.assertFalse(data)
                mock_get.assert_not_called()

    def test_host_resolving_to_private_ip_refused(self):
        for ip in ("127.0.0.1", "10.1.2.3", "169.254.169.254", "::1", "fc00::5"):
            with self.subTest(ip=ip):
                data, mock_get, _dns = self._load("https://images.example.com/a.png", ips=(PUBLIC_IP, ip))
                self.assertFalse(data)
                mock_get.assert_not_called()

    def test_unresolvable_host_refused(self):
        with (
            patch(GETADDRINFO, side_effect=OSError("no such host")),
            patch(REQUESTS_GET) as mock_get,
        ):
            self.assertFalse(self.template._load_image_from_url(URL))
        mock_get.assert_not_called()

    def test_non_http_schemes_refused(self):
        for url in ("file:///etc/passwd", "ftp://example.com/a.png", "gopher://example.com/", "http:///a.png"):
            with self.subTest(url=url):
                data, mock_get, _dns = self._load(url)
                self.assertFalse(data)
                mock_get.assert_not_called()

    def test_redirect_to_private_ip_refused(self):
        redirect = _response(b"", content_type="text/html", status_code=302, location="http://169.254.169.254/x")
        data, mock_get, _dns = self._load(URL, responses=[redirect, _response(self.png)])
        self.assertFalse(data)
        mock_get.assert_called_once()

    def test_redirect_to_public_url_followed(self):
        redirect = _response(b"", content_type="text/html", status_code=301, location="/img/b.png")
        data, mock_get, _dns = self._load(URL, responses=[redirect, _response(self.png)])
        self.assertEqual(data, base64.b64encode(self.png))
        self.assertEqual(mock_get.call_args_list[1].args[0], "https://example.com/img/b.png")

    def test_too_many_redirects_refused(self):
        redirects = [_response(b"", content_type="text/html", status_code=302, location=f"/r{i}") for i in range(10)]
        data, mock_get, _dns = self._load(URL, responses=redirects)
        self.assertFalse(data)
        self.assertEqual(mock_get.call_count, 6)

    def test_too_large_response_refused(self):
        big = self.png + b"\0" * (10 * 1024 * 1024)
        data, _get, _dns = self._load(URL, responses=[_response(big)])
        self.assertFalse(data)
        data, _get, _dns = self._load(URL, responses=[_response(self.png, content_length=50 * 1024 * 1024)])
        self.assertFalse(data)

    def test_non_image_content_type_refused(self):
        data, _get, _dns = self._load(URL, responses=[_response(self.png, content_type="text/html")])
        self.assertFalse(data)

    def test_http_error_refused(self):
        data, _get, _dns = self._load(URL, responses=[_response(self.png, status_code=404)])
        self.assertFalse(data)

    def test_public_method_not_exposed(self):
        self.assertFalse(hasattr(self.template, "load_image_from_url"))

    def test_read_only_user_cannot_trigger_fetch(self):
        user = new_test_user(self.env, login="url_image_reader", groups="base.group_user")
        self.assertFalse(self.template.with_user(user).has_access("write"))
        template = self.env["product.template"].with_user(user).new({"name": "Onchange"})
        with (
            patch(GETADDRINFO, return_value=_addrinfo(PUBLIC_IP)),
            patch(REQUESTS_GET, return_value=_response(self.png)) as mock_get,
        ):
            self.assertFalse(template._load_image_from_url(URL))
            template.image_file_name = URL
            template.onchange_image_file_name()
        mock_get.assert_not_called()
