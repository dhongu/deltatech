import base64
import io
import sys
import unittest
from unittest.mock import patch

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageStat

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from odoo.addons.deltatech_image_optimize.models import watermark
from odoo.addons.deltatech_image_optimize.models.ir_attachment import _webp_available

SIZE = (600, 400)
LOGO_COLOR = (30, 120, 65)
MAX_DROP = 41  # cât scade alfa în interiorul siglei
MAX_OPACITY = 0.19


def _original():
    """Fundal alb în stânga, produs închis la culoare în dreapta, o zonă gri la mijloc."""
    img = Image.new("RGB", SIZE, (255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle((300, 0, 600, 400), fill=(40, 40, 45))
    draw.rectangle((220, 150, 380, 250), fill=(150, 150, 150))
    return img


def _logo_mask():
    """Sigle rotunde, cu margini netezite, repetate pe toată imaginea (ca un mozaic)."""
    mask = Image.new("L", SIZE, 0)
    draw = ImageDraw.Draw(mask)
    for x in range(40, SIZE[0], 110):
        for y in range(40, SIZE[1], 110):
            draw.ellipse((x, y, x + 30, y + 30), fill=255)
            draw.rectangle((x + 34, y + 8, x + 70, y + 20), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(1.5))


def _watermarked(original):
    """Amestecă sigla și scade transparența, cum face programul de watermark."""
    mask = _logo_mask()
    # opacitatea siglei e proporțională cu scăderea transparenței
    out = Image.composite(Image.new("RGB", SIZE, LOGO_COLOR), original, mask.point(lambda v: round(v * MAX_OPACITY)))
    out.putalpha(mask.point(lambda v: 255 - round(v * MAX_DROP / 255)))
    return out


def _png(img):
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@tagged("post_install", "-at_install")
class TestImageWatermark(TransactionCase):
    @classmethod
    def setUpClass(cls):
        if not watermark.numpy_available():
            raise unittest.SkipTest("numpy lipsește; eliminarea watermark-ului nu poate fi testată")
        super().setUpClass()
        cls.original = _original()
        cls.image = _png(_watermarked(cls.original))
        cls.product = cls.env["product.template"].create({"name": "WM Test", "image_1920": cls.image})
        cls.plain = cls.env["product.template"].create({"name": "WM Plain", "image_1920": _png(cls.original)})

    def _set_param(self, key, value):
        self.env["ir.config_parameter"].sudo().set_str(f"deltatech_image_optimize.{key}", value)

    def _wizard(self, records):
        action = records.action_dt_remove_watermark()
        return self.env[action["res_model"]].browse(action["res_id"])

    def _difference(self, data):
        _webp_available()
        result = Image.open(io.BytesIO(data)).convert("RGB")
        return ImageStat.Stat(ImageChops.difference(result, self.original)).mean

    # === funcțiile de imagine ===#

    def test_trace_is_not_a_cutout(self):
        self.assertTrue(watermark.has_alpha_trace(_watermarked(self.original)))
        # un produs decupat are transparență reală (alfa 0), nu urma unui watermark
        cutout = self.original.convert("RGBA")
        cutout.putalpha(_logo_mask().point(lambda v: 255 - v))
        self.assertFalse(watermark.has_alpha_trace(cutout))
        self.assertFalse(watermark.has_alpha_trace(self.original.convert("RGBA")))

    def test_learned_blend_restores_the_original(self):
        model = watermark.learn_alpha_trace([_watermarked(self.original)])
        self.assertTrue(model)
        self.assertAlmostEqual(model["t"][MAX_DROP], MAX_OPACITY, delta=0.03)

        clean = watermark.remove_alpha_trace(_watermarked(self.original), model)
        self.assertEqual(clean.mode, "RGB")
        for channel in ImageStat.Stat(ImageChops.difference(clean, self.original)).mean:
            self.assertLess(channel, 1.0)

    # === asistentul ===#

    def test_preview_then_apply(self):
        wizard = self._wizard(self.product)

        self.assertEqual(wizard.mode, "preview")
        self.assertTrue(wizard.preview, "the detected watermark is shown")
        self.assertEqual(self.product.image_1920.to_base64(), self.image, "the preview writes nothing")
        line = wizard.line_ids
        self.assertTrue(line.to_apply)
        for channel in self._difference(line.image_after.content):
            self.assertLess(channel, 1.0)

        wizard.action_apply()
        self.assertEqual(self.product.wm_removal_state, "done")
        self.assertEqual(self.product.wm_profile_id, wizard.profile_id)
        stored = self.product.image_1920.content
        self.assertFalse(watermark.has_alpha_trace(Image.open(io.BytesIO(stored)).convert("RGBA")))
        # după aplicare imaginea opacă e recodată (JPEG): diferența rămâne mică
        for channel in self._difference(stored):
            self.assertLess(channel, 4.0)

    def test_image_without_watermark_stays(self):
        wizard = self._wizard(self.product | self.plain)

        line = wizard.line_ids.filtered(lambda line: line.res_id == self.plain.id)
        self.assertFalse(line.image_after)
        self.assertFalse(line.to_apply)
        self.assertTrue(line.warning)
        self.assertEqual(wizard.failed_count, 1)
        wizard.action_apply()
        self.assertFalse(self.plain.wm_removal_state)

    def test_selection_without_watermark_raises(self):
        with self.assertRaises(UserError):
            self._wizard(self.plain)

    def test_large_selection_is_queued(self):
        self._set_param("wm_sync_limit", "0")
        wizard = self._wizard(self.product | self.plain)

        self.assertEqual(wizard.mode, "queue")
        self.assertFalse(any(wizard.line_ids.mapped("image_after")), "no preview is computed for a queue")
        wizard.action_apply()
        self.assertEqual(self.product.wm_removal_state, "pending")
        with patch.object(self.env.cr, "commit", lambda: None):
            self.env["ir.attachment"]._dt_wm_remove_cron()
        self.assertEqual(self.product.wm_removal_state, "done")
        self.assertEqual(self.plain.wm_removal_state, "error", "no watermark trace: left unchanged")

    def test_missing_numpy_raises(self):
        with patch.object(watermark, "numpy_available", lambda: False), self.assertRaises(UserError):
            self._wizard(self.product)

    def test_numpy_import_error_is_detected(self):
        with patch.dict(sys.modules, {"numpy": None}):
            self.assertFalse(watermark.numpy_available())

    # === învățarea ===#

    def test_nothing_to_learn(self):
        self.assertIsNone(watermark.learn_alpha_trace([]))
        self.assertIsNone(watermark.learn_alpha_trace([self.original.convert("RGBA")]))

    def test_large_image_is_reduced_before_learning(self):
        with patch.object(watermark, "LEARN_SIDE", 300):
            model = watermark.learn_alpha_trace([_watermarked(self.original)])
        self.assertTrue(model)
        self.assertAlmostEqual(model["t"][MAX_DROP], MAX_OPACITY, delta=0.05)

    def test_learn_limit_stops_early(self):
        self._set_param("wm_learn_limit", "1")
        other = self.env["product.template"].create({"name": "WM Test 2", "image_1920": self.image})
        wizard = self._wizard(self.product | other)

        self.assertEqual(wizard.learned_count, 1)
        self.assertEqual(len(wizard.line_ids), 2)

    def test_watermark_over_uniform_background_cannot_be_learned(self):
        # fără zone închise sub siglă, opacitatea nu se poate separa de culoare
        white = Image.new("RGB", SIZE, (255, 255, 255))
        product = self.env["product.template"].create({"name": "WM White", "image_1920": _png(_watermarked(white))})
        with self.assertRaisesRegex(UserError, "could not be learned"):
            self._wizard(product)

    # === coada ===#

    @mute_logger("odoo.addons.deltatech_image_optimize.models.image_watermark")
    def test_broken_image_in_queue_is_marked_failed(self):
        profile = self._wizard(self.product).profile_id
        self.product.write({"wm_removal_state": "pending", "wm_profile_id": profile.id})
        with (
            patch.object(type(profile), "_dt_clean", side_effect=OSError("cannot identify image file")),
            patch.object(self.env.cr, "commit", lambda: None),
        ):
            self.env["ir.attachment"]._dt_wm_remove_cron()

        self.assertEqual(self.product.wm_removal_state, "error")
        self.assertEqual(self.product.image_1920.to_base64(), self.image)

    def test_queue_larger_than_batch_triggers_again(self):
        self._set_param("wm_batch", "1")
        other = self.env["product.template"].create({"name": "WM Test 2", "image_1920": self.image})
        profile = self._wizard(self.product).profile_id
        (self.product | other).write({"wm_removal_state": "pending", "wm_profile_id": profile.id})
        cron = type(self.env["ir.cron"])
        with patch.object(cron, "_trigger") as trigger, patch.object(self.env.cr, "commit", lambda: None):
            self.env["ir.attachment"]._dt_wm_remove_cron()

        states = (self.product | other).mapped("wm_removal_state")
        self.assertEqual(sorted(states), ["done", "pending"])
        trigger.assert_called_once()
