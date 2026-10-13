# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io
from unittest.mock import MagicMock, patch

from PIL import Image

from odoo.tests import Form, TransactionCase, tagged

MODELS = "odoo.addons.deltatech_website_product_url_image.models.product_template"
REQUESTS_GET = MODELS + ".requests.get"
GETADDRINFO = MODELS + ".socket.getaddrinfo"
URL = "https://example.com/images/photo.png"
PUBLIC_IP = "93.184.216.34"


def _addrinfo(*ips):
    return [(2, 1, 6, "", (ip, 443)) for ip in ips]


def _png_bytes(color="red"):
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), color).save(buf, format="PNG")
    return buf.getvalue()


def _response(content, content_type="image/png", status_code=200, location=None, content_length=None):
    resp = MagicMock()
    resp.__enter__.return_value = resp
    resp.__exit__.return_value = False
    resp.status_code = status_code
    resp.is_redirect = location is not None
    headers = {"content-type": content_type}
    if location is not None:
        headers["location"] = location
    if content_length is not None:
        headers["content-length"] = str(content_length)
    resp.headers = headers
    resp.iter_content.side_effect = lambda size: (content[i : i + size] for i in range(0, len(content), size))
    return resp


@tagged("post_install", "-at_install")
class TestProductUrlImage(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.png = _png_bytes()
        cls.png_b64 = base64.b64encode(cls.png)
        cls.template = cls.env["product.template"].create({"name": "Test URL Image Product", "type": "consu"})

    def setUp(self):
        super().setUp()
        # no real DNS: every host name resolves to a public address
        patcher = patch(GETADDRINFO, return_value=_addrinfo(PUBLIC_IP))
        self.mock_getaddrinfo = patcher.start()
        self.addCleanup(patcher.stop)

    # ---------- _load_image_from_url ----------
    def test_load_image_from_url_valid(self):
        with patch(REQUESTS_GET, return_value=_response(self.png)) as mock_get:
            data = self.template._load_image_from_url("  " + URL + "  ")
        mock_get.assert_called_once_with(URL, timeout=15, stream=True, allow_redirects=False)
        self.assertEqual(data, self.png_b64)

    def test_load_image_from_url_invalid_content(self):
        with patch(REQUESTS_GET, return_value=_response(b"this is not an image")):
            data = self.template._load_image_from_url(URL)
        self.assertFalse(data)

    def test_load_image_from_url_request_error(self):
        with patch(REQUESTS_GET, side_effect=Exception("connection refused")):
            data = self.template._load_image_from_url(URL)
        self.assertFalse(data)

    # ---------- product.template write ----------
    def test_template_write_url_loads_image(self):
        with patch(REQUESTS_GET, return_value=_response(self.png)):
            self.template.write({"image_file_name": URL})
        self.assertEqual(self.template.image_file_name, "photo.png")
        self.assertTrue(self.template.image_1920)

    def test_template_write_url_invalid_image_keeps_name(self):
        with patch(REQUESTS_GET, return_value=_response(b"garbage")):
            self.template.write({"image_file_name": URL})
        self.assertEqual(self.template.image_file_name, URL)
        self.assertFalse(self.template.image_1920)

    def test_template_write_plain_name(self):
        with patch(REQUESTS_GET) as mock_get:
            self.template.write({"image_file_name": "local_file.png"})
        mock_get.assert_not_called()
        self.assertEqual(self.template.image_file_name, "local_file.png")
        self.assertFalse(self.template.image_1920)

    def test_template_write_other_fields(self):
        with patch(REQUESTS_GET) as mock_get:
            self.template.write({"name": "Renamed"})
        mock_get.assert_not_called()
        self.assertEqual(self.template.name, "Renamed")

    # ---------- product.template onchange ----------
    def test_template_onchange_url(self):
        with patch(REQUESTS_GET, return_value=_response(self.png)):
            with Form(self.template) as form:
                form.image_file_name = URL
                self.assertEqual(form.image_file_name, "photo.png")
        self.assertEqual(self.template.image_file_name, "photo.png")
        self.assertTrue(self.template.image_1920)

    def test_template_onchange_direct(self):
        template = self.env["product.template"].new({"name": "New"})
        template.image_file_name = False
        with patch(REQUESTS_GET) as mock_get:
            template.onchange_image_file_name()
        mock_get.assert_not_called()

        template.image_file_name = "no_scheme.png"
        with patch(REQUESTS_GET) as mock_get:
            template.onchange_image_file_name()
        mock_get.assert_not_called()
        self.assertEqual(template.image_file_name, "no_scheme.png")

        template.image_file_name = URL
        with patch(REQUESTS_GET, return_value=_response(b"garbage")):
            template.onchange_image_file_name()
        self.assertEqual(template.image_file_name, URL)
        self.assertFalse(template.image_1920)

        with patch(REQUESTS_GET, return_value=_response(self.png)):
            template.onchange_image_file_name()
        self.assertEqual(template.image_file_name, "photo.png")
        self.assertTrue(template.image_1920)

    # ---------- product.image ----------
    def _create_product_image(self):
        return self.env["product.image"].create(
            {"name": "initial", "product_tmpl_id": self.template.id, "image_1920": base64.b64encode(_png_bytes("blue"))}
        )

    def test_product_image_write_url(self):
        product_image = self._create_product_image()
        with patch(REQUESTS_GET, return_value=_response(self.png)):
            product_image.write({"name": URL})
        self.assertEqual(product_image.name, "photo.png")
        self.assertTrue(product_image.image_1920)

    def test_product_image_write_url_invalid(self):
        product_image = self._create_product_image()
        old_image = product_image.image_1920
        with patch(REQUESTS_GET, return_value=_response(b"garbage")):
            product_image.write({"name": URL})
        self.assertEqual(product_image.name, URL)
        self.assertEqual(product_image.image_1920, old_image)

    def test_product_image_write_plain_name(self):
        product_image = self._create_product_image()
        with patch(REQUESTS_GET) as mock_get:
            product_image.write({"name": "plain name"})
            product_image.write({"sequence": 5})
        mock_get.assert_not_called()
        self.assertEqual(product_image.name, "plain name")

    def test_product_image_onchange_name(self):
        product_image = self.env["product.image"].new({"name": "plain", "product_tmpl_id": self.template.id})
        with patch(REQUESTS_GET) as mock_get:
            product_image.onchange_name()
        mock_get.assert_not_called()
        self.assertEqual(product_image.name, "plain")

        product_image.name = URL
        with patch(REQUESTS_GET, return_value=_response(b"garbage")):
            product_image.onchange_name()
        self.assertEqual(product_image.name, URL)

        with patch(REQUESTS_GET, return_value=_response(self.png)):
            product_image.onchange_name()
        self.assertEqual(product_image.name, "photo.png")
        self.assertTrue(product_image.image_1920)
