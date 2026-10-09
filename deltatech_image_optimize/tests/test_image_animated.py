import base64
import io
import os

from odoo.tests import TransactionCase, tagged

try:
    from PIL import Image

    from odoo.addons.deltatech_image_optimize.models.ir_attachment import _webp_available

    WEBP_OK = _webp_available()
except ImportError:
    Image = None
    WEBP_OK = False


@tagged("post_install", "-at_install")
class TestImageAnimated(TransactionCase):
    """IMAGE-001: animated images are never flattened to their first frame."""

    def setUp(self):
        super().setUp()
        if Image is None:
            self.skipTest("Pillow not available")
        self.Attachment = self.env["ir.attachment"]

    def _frames(self, size=400, count=4):
        # Noisy frames: a JPEG of the first frame is much smaller than the
        # animation, so the old code always "won" by flattening it.
        return [Image.frombytes("RGB", (size, size), os.urandom(size * size * 3)) for _i in range(count)]

    def _animated(self, fmt, size=400, count=4):
        frames = self._frames(size, count)
        buf = io.BytesIO()
        extra = {"lossless": True} if fmt == "WEBP" else {}
        frames[0].save(buf, format=fmt, save_all=True, append_images=frames[1:], duration=120, loop=0, **extra)
        return buf.getvalue()

    def _static_png(self, size=400):
        buf = io.BytesIO()
        self._frames(size, 1)[0].save(buf, format="PNG")
        return buf.getvalue()

    def _recompress(self, raw):
        return self.Attachment._dt_image_recompress(raw, 70, 1920, 85, False)

    def _n_frames(self, raw):
        return getattr(Image.open(io.BytesIO(raw)), "n_frames", 1)

    def test_animated_png_is_skipped(self):
        raw = self._animated("PNG")
        self.assertEqual(self._n_frames(raw), 4)
        self.assertEqual(self._recompress(raw), (None, None))

    def test_animated_webp_is_skipped(self):
        if not WEBP_OK:
            self.skipTest("WebP not available")
        raw = self._animated("WEBP")
        self.assertEqual(self._n_frames(raw), 4)
        self.assertEqual(self._recompress(raw), (None, None))

    def test_animated_gif_is_skipped(self):
        raw = self._animated("GIF")
        self.assertEqual(self._recompress(raw), (None, None))

    def test_static_png_still_optimized(self):
        raw = self._static_png()
        data, out_format = self._recompress(raw)
        self.assertEqual(out_format, "JPEG")
        self.assertLess(len(data), len(raw))

    def test_static_webp_still_optimized(self):
        if not WEBP_OK:
            self.skipTest("WebP not available")
        buf = io.BytesIO()
        self._frames(400, 1)[0].save(buf, format="WEBP", lossless=True)
        raw = buf.getvalue()
        data, out_format = self._recompress(raw)
        self.assertEqual(out_format, "JPEG")
        self.assertLess(len(data), len(raw))

    def _image_att(self, partner, field):
        return self.Attachment.sudo().search(
            [("res_model", "=", "res.partner"), ("res_id", "=", partner.id), ("res_field", "=", field)],
            limit=1,
        )

    def test_runners_keep_animated_png(self):
        """Both batch runners leave an APNG attachment byte-for-byte unchanged."""
        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")
        ICP.set_param("deltatech_image_optimize.variant_min_size", "1")
        ICP.set_param("deltatech_image_optimize.variant_fields", "image_1024")
        raw = self._animated("PNG")
        partner = self.env["res.partner"].create({"name": "APNG Test", "image_1920": base64.b64encode(raw)})
        _ = partner.image_1024  # materialize the variant attachment
        self.env.flush_all()
        att = self._image_att(partner, "image_1920")
        var = self._image_att(partner, "image_1024")
        self.assertEqual(self._n_frames(att.raw), 4)
        var_raw = var.raw

        self.Attachment._dt_image_optimize_run(limit=50)
        self.Attachment._dt_image_optimize_variants_run(limit=50)

        att = self._image_att(partner, "image_1920")
        att.invalidate_recordset()
        self.assertEqual(att.raw, raw)
        self.assertEqual(self._n_frames(att.raw), 4)
        self.assertTrue(att.deltatech_image_optimized)
        if var:
            var.invalidate_recordset()
            self.assertEqual(var.raw, var_raw)
