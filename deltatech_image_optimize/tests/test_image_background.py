import base64
import io
from unittest.mock import patch

from PIL import ImageChops

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.deltatech_image_optimize.models import image_background
from odoo.addons.deltatech_image_optimize.models.ir_attachment import Image, _webp_available

BG_COLOR = (120, 200, 120)
PRODUCT_COLOR = (90, 90, 95)


def _fake_cutout(img, model_name):
    """Stă în locul lui rembg: tot ce are culoarea fundalului devine transparent."""
    diff = ImageChops.difference(img.convert("RGB"), Image.new("RGB", img.size, BG_COLOR))
    rgba = img.convert("RGBA")
    rgba.putalpha(diff.convert("L").point(lambda v: 255 if v else 0))
    return rgba


@tagged("post_install", "-at_install")
class TestImageBackground(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        img = Image.new("RGB", (400, 300), BG_COLOR)
        img.paste(Image.new("RGB", (200, 50), PRODUCT_COLOR), (50, 100))
        # PNG, nu JPEG: cutout-ul fals compară culorile exact
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        cls.image = base64.b64encode(buf.getvalue())
        cls.product = cls.env["product.template"].create({"name": "BG Test", "image_1920": cls.image})

    def setUp(self):
        super().setUp()
        self.startPatcher(patch.object(image_background, "_rembg_cutout", _fake_cutout))
        self.startPatcher(patch.object(image_background, "_rembg_available", lambda: True))

    def _set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_param(f"deltatech_image_optimize.{key}", value)

    def _attachment(self, record, field):
        return (
            self.env["ir.attachment"]
            .sudo()
            .search([("res_model", "=", record._name), ("res_id", "=", record.id), ("res_field", "=", field)])
        )

    def _decoded(self, record, field="image_1920"):
        _webp_available()
        return Image.open(io.BytesIO(base64.b64decode(record[field])))

    def test_remove_background_keeps_original_and_writes_webp(self):
        self.product.action_dt_remove_background()

        self.assertEqual(self.product.bg_removal_state, "done")
        self.assertEqual(self.product.image_bg_original, self.image)
        result = self._decoded(self.product)
        self.assertEqual(result.size, (400, 300), "without crop the canvas stays the same")
        self.assertEqual(result.convert("RGBA").getpixel((5, 5))[3], 0, "the background is transparent")
        self.assertEqual(result.convert("RGBA").getpixel((150, 125))[3], 255, "the product stays opaque")
        if _webp_available():
            self.assertEqual(self._attachment(self.product, "image_1920").mimetype, "image/webp")
            variant = self._attachment(self.product, "image_128")
            self.assertEqual(variant.mimetype, "image/webp")
            # Odoo nu redimensionează WebP: variantele trebuie generate înainte de conversie
            self.assertLessEqual(max(Image.open(io.BytesIO(variant.raw)).size), 128)

    def test_restore_background(self):
        self.product.action_dt_remove_background()
        self.product.action_dt_restore_background()

        self.assertEqual(self.product.image_1920, self.image)
        self.assertFalse(self.product.image_bg_original)
        self.assertFalse(self.product.bg_removal_state)

    def test_second_pass_keeps_real_original(self):
        self.product.action_dt_remove_background()
        self.product.action_dt_remove_background()

        self.assertEqual(self.product.image_bg_original, self.image)

    def test_crop_square_with_margin(self):
        self._set_param("bg_crop", "1")
        self._set_param("bg_margin", "10")
        self.product.action_dt_remove_background()

        # produsul are 200 px pe latura lungă, plus 10% margine pe fiecare parte
        self.assertEqual(self._decoded(self.product).size, (240, 240))

    def test_solid_color_background(self):
        self._set_param("bg_color", "#FFFFFF")
        self.product.action_dt_remove_background()

        result = self._decoded(self.product).convert("RGB")
        self.assertEqual(result.getpixel((5, 5)), (255, 255, 255))

    def test_gallery_images_are_included(self):
        extra = self.env["product.image"].create(
            {"name": "extra", "image_1920": self.image, "product_tmpl_id": self.product.id}
        )
        self.product.action_dt_remove_background()

        self.assertEqual(extra.bg_removal_state, "done")
        self.assertEqual(extra.image_checksum, self._attachment(extra, "image_1920").checksum)
        self.product.action_dt_restore_background()
        self.assertEqual(extra.image_1920, self.image)

    def test_large_selection_is_queued_for_cron(self):
        self._set_param("bg_sync_limit", "0")
        self.product.action_dt_remove_background()
        self.assertEqual(self.product.bg_removal_state, "pending")

        with patch.object(self.env.cr, "commit", lambda: None):
            self.env["ir.attachment"]._dt_bg_remove_cron()
        self.assertEqual(self.product.bg_removal_state, "done")

    def test_empty_cutout_marks_error(self):
        with patch.object(image_background, "_rembg_cutout", lambda img, m: img.convert("RGBA").point(lambda v: 0)):
            self.product.action_dt_remove_background()

        self.assertEqual(self.product.bg_removal_state, "error")
        self.assertEqual(self.product.image_1920, self.image)
        self.assertFalse(self.product.image_bg_original)

    def test_missing_rembg_raises(self):
        with patch.object(image_background, "_rembg_available", lambda: False), self.assertRaises(UserError):
            self.product.action_dt_remove_background()
