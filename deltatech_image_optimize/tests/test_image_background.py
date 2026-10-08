import base64
import io
from unittest.mock import patch

from PIL import ImageChops

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.deltatech_image_optimize.models import image_background, ir_attachment
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
        self.startPatcher(patch.object(ir_attachment, "_rembg_cutout", _fake_cutout))
        self.startPatcher(patch.object(image_background, "_rembg_available", lambda: True))
        self.startPatcher(patch.object(ir_attachment, "_rembg_available", lambda: True))

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

    def _run(self, records, untick=None):
        """Rulează acțiunea și aplică wizard-ul, ca utilizatorul."""
        action = records.action_dt_remove_background()
        wizard = self.env[action["res_model"]].browse(action["res_id"])
        if untick:
            wizard.line_ids.filtered(lambda line: line.res_id in untick.ids).to_apply = False
        wizard.action_apply()
        return wizard

    def test_preview_then_apply_writes_webp(self):
        action = self.product.action_dt_remove_background()
        wizard = self.env[action["res_model"]].browse(action["res_id"])

        self.assertEqual(wizard.mode, "preview")
        self.assertEqual(self.product.image_1920, self.image, "the preview writes nothing")
        self.assertTrue(wizard.line_ids.image_after)
        wizard.action_apply()

        self.assertEqual(self.product.bg_removal_state, "done")
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

    def test_unticked_line_is_not_applied(self):
        self._run(self.product, untick=self.product)

        self.assertEqual(self.product.image_1920, self.image)
        self.assertFalse(self.product.bg_removal_state)

    def test_crop_square_with_margin(self):
        self._set_param("bg_crop", "1")
        self._set_param("bg_margin", "10")
        self._run(self.product)

        # produsul are 200 px pe latura lungă, plus 10% margine pe fiecare parte
        self.assertEqual(self._decoded(self.product).size, (240, 240))

    def test_solid_color_background(self):
        self._set_param("bg_color", "#FFFFFF")
        self._run(self.product)

        result = self._decoded(self.product).convert("RGB")
        self.assertEqual(result.getpixel((5, 5)), (255, 255, 255))

    def test_gallery_images_are_included(self):
        extra = self.env["product.image"].create(
            {"name": "extra", "image_1920": self.image, "product_tmpl_id": self.product.id}
        )
        wizard = self._run(self.product)

        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(extra.bg_removal_state, "done")
        self.assertEqual(extra.image_checksum, self._attachment(extra, "image_1920").checksum)

    def test_large_selection_is_queued_for_cron(self):
        self._set_param("bg_sync_limit", "0")
        wizard = self._run(self.product)

        self.assertEqual(wizard.mode, "queue")
        self.assertFalse(wizard.line_ids.image_after, "no preview is computed for a queue")
        self.assertEqual(self.product.bg_removal_state, "pending")
        with patch.object(self.env.cr, "commit", lambda: None):
            self.env["ir.attachment"]._dt_bg_remove_cron()
        self.assertEqual(self.product.bg_removal_state, "done")

    def test_empty_cutout_is_not_applied(self):
        self._set_param("bg_method", "rembg")
        with patch.object(ir_attachment, "_rembg_cutout", lambda img, m: img.convert("RGBA").point(lambda v: 0)):
            wizard = self._run(self.product)

        self.assertEqual(wizard.failed_count, 1)
        self.assertFalse(wizard.line_ids.to_apply)
        self.assertEqual(self.product.image_1920, self.image)

    def test_missing_rembg_raises(self):
        self._set_param("bg_method", "rembg")
        with patch.object(image_background, "_rembg_available", lambda: False), self.assertRaises(UserError):
            self.product.action_dt_remove_background()

    # === uniform background ===#

    def _product_with(self, draw, background=BG_COLOR):
        """Un produs nou, cu imaginea desenată de ``draw`` peste imaginea de bază."""
        img = Image.new("RGB", (400, 300), background)
        img.paste(Image.new("RGB", (200, 50), PRODUCT_COLOR), (50, 100))
        draw(img)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return self.env["product.template"].create({"name": "BG Extra", "image_1920": base64.b64encode(buf.getvalue())})

    @staticmethod
    def _accessory(img):
        # accesoriu închis la culoare, separat de produs, ca pâlnia de lângă flacon
        img.paste(Image.new("RGB", (40, 60), (15, 15, 15)), (300, 80))

    def test_uniform_background_keeps_accessory(self):
        product = self._product_with(self._accessory)
        self._run(product)

        result = self._decoded(product).convert("RGBA")
        self.assertEqual(result.getpixel((320, 110))[3], 255, "the accessory stays")
        self.assertEqual(result.getpixel((150, 125))[3], 255)
        self.assertEqual(result.getpixel((5, 5))[3], 0)

    def test_ai_model_dropping_accessory_is_flagged(self):
        def drops_accessory(img, model_name):
            rgba = _fake_cutout(img, model_name)
            rgba.paste((0, 0, 0, 0), (290, 70, 350, 150))
            return rgba

        product = self._product_with(self._accessory)
        self._set_param("bg_method", "rembg")
        with patch.object(ir_attachment, "_rembg_cutout", drops_accessory):
            action = product.action_dt_remove_background()
        wizard = self.env[action["res_model"]].browse(action["res_id"])

        self.assertTrue(wizard.line_ids.image_after)
        self.assertTrue(wizard.line_ids.warning)
        self.assertFalse(wizard.line_ids.to_apply, "a suspicious cut-out is unticked")
        self.assertEqual(wizard.warning_count, 1)

        # aceeași imagine, refăcută din wizard cu fundalul uniform, nu mai e suspectă
        wizard.method = "uniform"
        wizard.action_refresh()
        self.assertFalse(wizard.line_ids.warning)
        self.assertTrue(wizard.line_ids.to_apply)

    def test_specks_are_removed(self):
        product = self._product_with(lambda img: img.paste(Image.new("RGB", (3, 3), (40, 40, 40)), (350, 250)))
        self._run(product)

        self.assertEqual(self._decoded(product).convert("RGBA").getpixel((351, 251))[3], 0)

    def test_white_inside_product_stays_opaque(self):
        # zonă de culoarea fundalului închisă în produs (eticheta albă a unui flacon)
        product = self._product_with(lambda img: img.paste(Image.new("RGB", (40, 20), BG_COLOR), (120, 115)))
        self._run(product)

        self.assertEqual(self._decoded(product).convert("RGBA").getpixel((140, 125))[3], 255)

    def test_without_rembg_only_uniform_backgrounds(self):
        def gradient(img):
            for x in range(img.width):
                img.paste((x * 255 // img.width, 80, 160), (x, 0, x + 1, 30))

        product = self._product_with(gradient)
        with (
            patch.object(image_background, "_rembg_available", lambda: False),
            patch.object(ir_attachment, "_rembg_available", lambda: False),
        ):
            action = (product | self.product).action_dt_remove_background()
        wizard = self.env[action["res_model"]].browse(action["res_id"])

        lines = {line.res_id: line for line in wizard.line_ids}
        self.assertFalse(lines[product.id].image_after, "a real background needs the AI model")
        self.assertIn("rembg", lines[product.id].warning)
        self.assertTrue(lines[self.product.id].image_after)

    def test_gallery_line_names_show_position(self):
        self.env["product.image"].create(
            {"name": "BG Test", "image_1920": self.image, "product_tmpl_id": self.product.id}
        )
        action = self.product.action_dt_remove_background()
        wizard = self.env[action["res_model"]].browse(action["res_id"])

        names = wizard.line_ids.mapped("name")
        self.assertIn("main image", names[0])
        self.assertIn("gallery image 1", names[1])
