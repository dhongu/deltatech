# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import contextlib
from unittest.mock import patch

import werkzeug.urls

from odoo.tests import TransactionCase, tagged

from .test_product_url_image import GETADDRINFO, PUBLIC_IP, REQUESTS_GET, URL, _addrinfo, _png_bytes, _response


@contextlib.contextmanager
def _werkzeug_3():
    """Simulate Werkzeug >= 3.0, where werkzeug.urls.url_parse was removed."""
    missing = object()
    original = getattr(werkzeug.urls, "url_parse", missing)
    if original is not missing:
        delattr(werkzeug.urls, "url_parse")
    try:
        yield
    finally:
        if original is not missing:
            werkzeug.urls.url_parse = original


@tagged("post_install", "-at_install")
class TestUrlImageWerkzeug3(TransactionCase):
    """#3496: URL detection must not depend on werkzeug.urls.url_parse (removed in Werkzeug 3)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.png = _png_bytes()
        cls.template = cls.env["product.template"].create({"name": "Werkzeug 3 Product", "type": "consu"})
        cls.product_image = cls.env["product.image"].create(
            {"name": "initial", "product_tmpl_id": cls.template.id, "image_1920": base64.b64encode(_png_bytes("blue"))}
        )

    def setUp(self):
        super().setUp()
        patcher = patch(GETADDRINFO, return_value=_addrinfo(PUBLIC_IP))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_template_write_without_url_parse(self):
        with _werkzeug_3(), patch(REQUESTS_GET) as mock_get:
            self.template.write({"image_file_name": "local_file.png"})
        mock_get.assert_not_called()
        self.assertEqual(self.template.image_file_name, "local_file.png")
        with _werkzeug_3(), patch(REQUESTS_GET, return_value=_response(self.png)):
            self.template.write({"image_file_name": URL})
        self.assertEqual(self.template.image_file_name, "photo.png")
        self.assertTrue(self.template.image_1920)
        with _werkzeug_3(), patch(REQUESTS_GET) as mock_get:
            self.template.write({"image_file_name": False})
        mock_get.assert_not_called()

    def test_template_onchange_without_url_parse(self):
        template = self.env["product.template"].new({"name": "New", "image_file_name": URL})
        with _werkzeug_3(), patch(REQUESTS_GET, return_value=_response(self.png)):
            template.onchange_image_file_name()
        self.assertEqual(template.image_file_name, "photo.png")

    def test_product_image_rename_without_url_parse(self):
        with _werkzeug_3(), patch(REQUESTS_GET) as mock_get:
            self.product_image.write({"name": "renamed image"})
        mock_get.assert_not_called()
        self.assertEqual(self.product_image.name, "renamed image")
        with _werkzeug_3(), patch(REQUESTS_GET, return_value=_response(self.png)):
            self.product_image.write({"name": URL})
        self.assertEqual(self.product_image.name, "photo.png")

    def test_product_image_onchange_without_url_parse(self):
        product_image = self.env["product.image"].new({"name": URL, "product_tmpl_id": self.template.id})
        with _werkzeug_3(), patch(REQUESTS_GET, return_value=_response(self.png)):
            product_image.onchange_name()
        self.assertEqual(product_image.name, "photo.png")
