# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64

from odoo.tests import TransactionCase, tagged
from odoo.tools import BinaryBytes

# 1x1 transparent PNG
PIXEL = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")


@tagged("post_install", "-at_install")
class TestWatermark(TransactionCase):
    def test_settings_write_company_watermark(self):
        """Watermark set in settings (base64 string, as sent over RPC) lands on the company."""
        settings = self.env["res.config.settings"].create({"watermark_image": base64.b64encode(PIXEL).decode()})
        settings.execute()
        self.assertEqual(self.env.company.watermark_image.content, PIXEL)

    def test_settings_read_company_watermark(self):
        self.env.company.watermark_image = BinaryBytes(PIXEL)
        settings = self.env["res.config.settings"].create({})
        self.assertEqual(settings.watermark_image.content, PIXEL)

    def test_settings_view(self):
        arch = self.env["res.config.settings"].get_view(view_type="form")["arch"]
        self.assertIn('id="watermark_image_setting"', arch)
        self.assertIn('name="watermark_image"', arch)
