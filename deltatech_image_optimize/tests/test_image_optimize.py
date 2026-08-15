import base64
import io
import os

from odoo.tests import TransactionCase, tagged

try:
    from PIL import Image

    # Ask the module itself instead of probing here: it registers Pillow's WebP
    # plugin first, which Odoo's preinit() leaves out. Probing directly at
    # import time reports "no WebP" on a Pillow that encodes WebP perfectly
    # well, and the test then skips itself for a reason that is not true.
    from odoo.addons.deltatech_image_optimize.models.ir_attachment import _webp_available

    WEBP_OK = _webp_available()
except ImportError:
    Image = None
    WEBP_OK = False


@tagged("post_install", "-at_install")
class TestImageOptimize(TransactionCase):
    def _make_big_jpeg(self, size=2200):
        """Build a noisy JPEG that is large and above the 1920 limit."""
        raw = os.urandom(size * size * 3)
        img = Image.frombytes("RGB", (size, size), raw)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
        return base64.b64encode(buf.getvalue())

    def _make_big_transparent_png(self, size=2000):
        """Build a large RGBA (transparent) PNG."""
        raw = os.urandom(size * size * 4)
        img = Image.frombytes("RGBA", (size, size), raw)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue())

    def _make_opaque_rgba_png(self, size=2000):
        """Build a large RGBA PNG whose alpha is fully opaque (255)."""
        img = Image.frombytes("RGB", (size, size), os.urandom(size * size * 3)).convert("RGBA")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue())

    def _image_attachment(self, partner):
        return (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", partner.id),
                    ("res_field", "=", "image_1920"),
                ],
                limit=1,
            )
        )

    def test_optimize_shrinks_and_flags(self):
        if Image is None:
            self.skipTest("Pillow not available")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.quality", "70")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")

        partner = self.env["res.partner"].create({"name": "Image Optimize Test", "image_1920": self._make_big_jpeg()})
        att = self._image_attachment(partner)
        self.assertTrue(att, "partner should have a stored image_1920 attachment")
        original_size = att.file_size
        self.assertFalse(att.deltatech_image_optimized)

        stats = self.env["ir.attachment"]._dt_image_optimize_run(limit=50)
        self.assertGreaterEqual(stats["optimized"], 1)

        new_att = self._image_attachment(partner)
        self.assertTrue(new_att)
        self.assertLess(new_att.file_size, original_size)
        self.assertTrue(new_att.deltatech_image_optimized)

        # The stored image must still be a valid image no larger than 1920 px.
        img = Image.open(io.BytesIO(new_att.raw))
        self.assertLessEqual(max(img.size), 1920)

    def test_second_run_is_idempotent(self):
        if Image is None:
            self.skipTest("Pillow not available")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.quality", "70")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")

        # Drain any pre-existing backlog (demo images from other installed
        # modules) so the run below only sees the attachment created here.
        Attachment = self.env["ir.attachment"]
        while Attachment._dt_image_optimize_run(limit=200)["scanned"]:
            pass

        self.env["res.partner"].create({"name": "Image Optimize Test 2", "image_1920": self._make_big_jpeg()})
        Attachment._dt_image_optimize_run(limit=50)
        # Everything processed is flagged, so a second run finds nothing new.
        stats = Attachment._dt_image_optimize_run(limit=50)
        self.assertEqual(stats["optimized"], 0)

    def test_transparent_image_becomes_webp(self):
        if Image is None:
            self.skipTest("Pillow not available")
        if not WEBP_OK:
            self.skipTest("Pillow build lacks WebP support")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.webp_quality", "80")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")

        partner = self.env["res.partner"].create(
            {"name": "Transparent Test", "image_1920": self._make_big_transparent_png()}
        )
        att = self._image_attachment(partner)
        self.assertTrue(att)
        original_size = att.file_size

        stats = self.env["ir.attachment"]._dt_image_optimize_run(limit=50)
        self.assertGreaterEqual(stats["optimized"], 1)

        new_att = self._image_attachment(partner)
        self.assertLess(new_att.file_size, original_size)
        self.assertEqual(new_att.mimetype, "image/webp")
        self.assertTrue(new_att.deltatech_image_optimized)
        # The stored image must still be a valid WebP that preserves alpha.
        img = Image.open(io.BytesIO(new_att.raw))
        self.assertEqual((img.format or "").upper(), "WEBP")
        self.assertIn(img.mode, ("RGBA", "LA"))  # transparency preserved

    def test_opaque_rgba_becomes_jpeg(self):
        if Image is None:
            self.skipTest("Pillow not available")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.quality", "70")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")

        partner = self.env["res.partner"].create(
            {"name": "Opaque RGBA Test", "image_1920": self._make_opaque_rgba_png()}
        )
        att = self._image_attachment(partner)
        original_size = att.file_size

        stats = self.env["ir.attachment"]._dt_image_optimize_run(limit=50)
        self.assertGreaterEqual(stats["optimized"], 1)

        new_att = self._image_attachment(partner)
        self.assertLess(new_att.file_size, original_size)
        # Opaque alpha -> flattened to JPEG (no WebP dependency).
        self.assertEqual(new_att.mimetype, "image/jpeg")

    def test_force_jpeg_ignores_transparency(self):
        if Image is None:
            self.skipTest("Pillow not available")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.quality", "70")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")
        ICP.set_param("deltatech_image_optimize.force_jpeg", "1")

        # A transparent PNG that would normally go to WebP:
        partner = self.env["res.partner"].create(
            {"name": "Force JPEG Test", "image_1920": self._make_big_transparent_png()}
        )
        att = self._image_attachment(partner)
        original_size = att.file_size

        stats = self.env["ir.attachment"]._dt_image_optimize_run(limit=50)
        self.assertGreaterEqual(stats["optimized"], 1)

        new_att = self._image_attachment(partner)
        self.assertLess(new_att.file_size, original_size)
        # force_jpeg -> JPEG regardless of the alpha channel.
        self.assertEqual(new_att.mimetype, "image/jpeg")

    def test_variant_optimize_keeps_original(self):
        if Image is None:
            self.skipTest("Pillow not available")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.variant_min_size", "1")
        ICP.set_param("deltatech_image_optimize.variant_quality", "60")

        partner = self.env["res.partner"].create({"name": "Variant Test", "image_1920": self._make_big_jpeg()})
        orig_att = self._image_attachment(partner)
        orig_1920 = orig_att.raw  # keep the master bytes to prove they don't change

        # Variants are stored lazily: read image_1024 to materialize its attachment.
        _ = partner.image_1024
        self.env.flush_all()

        var = (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [("res_model", "=", "res.partner"), ("res_id", "=", partner.id), ("res_field", "=", "image_1024")],
                limit=1,
            )
        )
        self.assertTrue(var, "image_1024 variant attachment should exist")
        before = var.file_size

        stats = self.env["ir.attachment"]._dt_image_optimize_variants_run(limit=50)
        self.assertGreaterEqual(stats["optimized"], 1)

        var.invalidate_recordset()
        self.assertLess(var.file_size, before)  # variant shrank
        self.assertTrue(var.deltatech_image_optimized)
        # the master image_1920 must be byte-for-byte unchanged (no propagation)
        self._image_attachment(partner).invalidate_recordset()
        self.assertEqual(self._image_attachment(partner).raw, orig_1920)
