# © 2026 Deltatech
# See README.rst file on addons root folder for license details

import base64
import os
import tempfile

from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_business_process.tools.md_to_html import _embed_images, fisa_md_to_html

# 1x1 transparent PNG
PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
)


class TestMdToHtml(TransactionCase):
    def test_fisa_md_to_html_missing_path(self):
        self.assertIsNone(fisa_md_to_html(False))
        self.assertIsNone(fisa_md_to_html(""))
        self.assertIsNone(fisa_md_to_html("/nonexistent/FISA_CONSULTANT.md"))

    def test_fisa_md_to_html_full_conversion(self):
        try:
            import markdown  # noqa: F401, PLC0415
        except ImportError:
            self.skipTest("python markdown library not installed")
        with tempfile.TemporaryDirectory() as tmp:
            os.mkdir(os.path.join(tmp, "screenshots"))
            with open(os.path.join(tmp, "screenshots", "01.png"), "wb") as fh:
                fh.write(PNG_BYTES)
            md_path = os.path.join(tmp, "FISA_CONSULTANT.md")
            with open(md_path, "w", encoding="utf-8") as fh:
                fh.write(
                    "# Title\n\n"
                    "Some **bold** text.\n\n"
                    "| A | B |\n|---|---|\n| 1 | 2 |\n\n"
                    "![local](screenshots/01.png)\n\n"
                    "![remote](https://example.com/x.png)\n\n"
                    "![missing](screenshots/missing.png)\n"
                )
            html = fisa_md_to_html(md_path)
        self.assertTrue(html.startswith("<!DOCTYPE html>"))
        self.assertIn("<h1>Title</h1>", html)
        self.assertIn("<table>", html)
        # local image embedded as base64
        self.assertIn("data:image/png;base64,", html)
        self.assertNotIn('src="screenshots/01.png"', html)
        # remote image left untouched
        self.assertIn('src="https://example.com/x.png"', html)
        # missing local image left untouched
        self.assertIn('src="screenshots/missing.png"', html)

    def test_embed_images_direct(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "img.jpg"), "wb") as fh:
                fh.write(PNG_BYTES)
            html = '<p><img alt="x" src="img.jpg"></p><img src="data:image/png;base64,AAA">'
            result = _embed_images(html, tmp)
        # extension drives the mimetype
        self.assertIn("data:image/jpg;base64,", result)
        # data: URIs are not re-embedded
        self.assertIn('src="data:image/png;base64,AAA"', result)
