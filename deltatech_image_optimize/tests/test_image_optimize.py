import base64
import io
import os
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

try:
    from PIL import Image

    # Ask the module itself instead of probing here: it registers Pillow's WebP
    # plugin first, which Odoo's preinit() leaves out. Probing directly at
    # import time reports "no WebP" on a Pillow that encodes WebP perfectly
    # well, and the test then skips itself for a reason that is not true.
    from odoo.addons.deltatech_image_optimize.models import ir_attachment
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

    def test_freed_disk_excludes_shared_files(self):
        """A picture used by two records frees disk only once, not twice."""
        if Image is None:
            self.skipTest("Pillow not available")

        ICP = self.env["ir.config_parameter"].sudo()
        ICP.set_param("deltatech_image_optimize.min_size", "1")
        ICP.set_param("deltatech_image_optimize.quality", "70")
        ICP.set_param("deltatech_image_optimize.target_fields", "image_1920")

        Attachment = self.env["ir.attachment"]
        while Attachment._dt_image_optimize_run(limit=200)["scanned"]:
            pass

        # The same bytes on two partners: Odoo keeps one file for both.
        image = self._make_big_jpeg()
        p1 = self.env["res.partner"].create({"name": "Shared A", "image_1920": image})
        p2 = self.env["res.partner"].create({"name": "Shared B", "image_1920": image})
        a1, a2 = self._image_attachment(p1), self._image_attachment(p2)
        self.assertEqual(a1.store_fname, a2.store_fname, "identical images should share one file")
        self.assertTrue(a1._dt_image_shared_file())

        stats = Attachment._dt_image_optimize_run(limit=50)
        self.assertEqual(stats["optimized"], 2)
        # Both attachments shrank, so `freed` counts both...
        self.assertGreater(stats["freed"], 0)
        # ...but the first rewrite left the old file in place for the second,
        # so at most one of the two can count as disk actually reclaimed.
        self.assertLess(stats["freed_disk"], stats["freed"])

    # === recompresia, fără înregistrări ===#

    def _noise_palette_png(self, size=400, transparent=True):
        """PNG paletizat din zgomot; cu ``transparent`` indexul 0 e transparent."""
        img = Image.frombytes("P", (size, size), os.urandom(size * size))
        img.putpalette(list(os.urandom(768)))
        buf = io.BytesIO()
        if transparent:
            img.save(buf, format="PNG", transparency=0)
        else:
            img.save(buf, format="PNG")
        return buf.getvalue()

    def test_unreadable_input_is_skipped(self):
        if Image is None:
            self.skipTest("Pillow not available")
        recompress = self.env["ir.attachment"]._dt_image_recompress
        self.assertEqual(recompress(b"", 85, 0), (None, None))
        self.assertEqual(recompress(b"this is not an image", 85, 0), (None, None))

    def test_without_pillow_nothing_runs(self):
        Attachment = self.env["ir.attachment"]
        empty = {"scanned": 0, "optimized": 0, "freed": 0, "freed_disk": 0}
        with patch.object(ir_attachment, "Image", None):
            self.assertEqual(Attachment._dt_image_recompress(b"raw", 85, 0), (None, None))
            self.assertEqual(Attachment._dt_image_optimize_run(), empty)
            self.assertEqual(Attachment._dt_image_optimize_variants_run(), empty)
            self.assertEqual(Attachment._dt_image_cutout(b"raw", {}), (None, ""))

    def test_palette_images_are_normalized_and_resized(self):
        if Image is None:
            self.skipTest("Pillow not available")
        recompress = self.env["ir.attachment"]._dt_image_recompress

        data, out_format = recompress(self._noise_palette_png(), 85, 100)
        self.assertEqual(out_format, "WEBP" if WEBP_OK else "PNG")
        img = Image.open(io.BytesIO(data))
        self.assertLessEqual(max(img.size), 100)
        self.assertIn(img.mode, ("RGBA", "LA"), "palette transparency becomes a real alpha channel")

        data, out_format = recompress(self._noise_palette_png(transparent=False), 85, 100)
        self.assertEqual(out_format, "JPEG")

    def test_transparent_image_without_webp_stays_png(self):
        if Image is None:
            self.skipTest("Pillow not available")
        raw = base64.b64decode(self._make_big_transparent_png(size=300))
        recompress = self.env["ir.attachment"]._dt_image_recompress

        with patch.object(ir_attachment, "_webp_available", lambda: False):
            data, out_format = recompress(raw, 85, 100)
        self.assertEqual(out_format, "PNG")
        self.assertEqual(Image.open(io.BytesIO(data)).mode, "RGBA")

        original_save = Image.Image.save

        def save_without_webp(img, fp, format=None, **params):  # pylint: disable=redefined-builtin
            if format == "WEBP":
                raise OSError("encoder webp not available")
            return original_save(img, fp, format=format, **params)

        with (
            patch.object(ir_attachment, "_webp_available", lambda: True),
            patch.object(Image.Image, "save", save_without_webp),
        ):
            data, out_format = recompress(raw, 85, 100)
        self.assertEqual(out_format, "PNG", "a failing WebP encoder falls back to PNG")

    # === rularea pe atașamente ===#

    def _set_params(self, **params):
        ICP = self.env["ir.config_parameter"].sudo()
        for key, value in params.items():
            ICP.set_param(f"deltatech_image_optimize.{key}", value)

    def test_result_not_smaller_is_flagged_and_kept(self):
        if Image is None:
            self.skipTest("Pillow not available")
        self._set_params(min_size="0", target_fields="image_1920")
        buf = io.BytesIO()
        Image.new("RGB", (16, 16), (200, 30, 30)).save(buf, format="PNG")
        partner = self.env["res.partner"].create({"name": "Tiny Image", "image_1920": base64.b64encode(buf.getvalue())})
        att = self._image_attachment(partner)
        raw = att.raw

        self.env["ir.attachment"]._dt_image_optimize_run(limit=1000)

        self.assertTrue(att.deltatech_image_optimized)
        self.assertEqual(att.raw, raw)

    def test_orphan_attachment_is_flagged(self):
        if Image is None:
            self.skipTest("Pillow not available")
        self._set_params(min_size="1", target_fields="image_1920")
        orphan = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": "image_1920",
                    "res_model": "res.partner",
                    "res_field": "image_1920",
                    "res_id": 2147483000,
                    "raw": base64.b64decode(self._make_big_jpeg(size=600)),
                }
            )
        )
        raw = orphan.raw

        self.env["ir.attachment"]._dt_image_optimize_run(limit=1000)

        self.assertTrue(orphan.deltatech_image_optimized)
        self.assertEqual(orphan.raw, raw, "nothing is written for a deleted record")

    def test_failed_record_write_is_flagged(self):
        if Image is None:
            self.skipTest("Pillow not available")
        self._set_params(min_size="1", target_fields="image_1920")
        partner = self.env["res.partner"].create({"name": "Write Fails", "image_1920": self._make_big_jpeg(size=600)})
        att = self._image_attachment(partner)
        raw = att.raw
        Partner = type(self.env["res.partner"])
        original_write = Partner.write

        def write(records, vals):
            if partner in records and "image_1920" in vals:
                raise ValueError("record is locked")
            return original_write(records, vals)

        with patch.object(Partner, "write", write):
            self.env["ir.attachment"]._dt_image_optimize_run(limit=1000)

        self.assertTrue(att.deltatech_image_optimized)
        self.assertEqual(att.raw, raw)

    def test_failed_variant_write_does_not_stop_the_batch(self):
        if Image is None:
            self.skipTest("Pillow not available")
        self._set_params(variant_min_size="1", variant_fields="image_1024,image_512")
        partner = self.env["res.partner"].create(
            {"name": "Variant Fails", "image_1920": self._make_big_jpeg(size=1200)}
        )
        _ = partner.image_1024, partner.image_512
        self.env.flush_all()
        variants = (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "res.partner"),
                    ("res_id", "=", partner.id),
                    ("res_field", "in", ["image_1024", "image_512"]),
                ]
            )
        )
        failing = variants.filtered(lambda att: att.res_field == "image_1024")
        Attachment = type(self.env["ir.attachment"])
        original_write = Attachment.write

        def write(records, vals):
            if failing in records and "deltatech_image_optimized" in vals:
                raise ValueError("storage unavailable")
            return original_write(records, vals)

        with patch.object(Attachment, "write", write):
            self.env["ir.attachment"]._dt_image_optimize_variants_run(limit=1000)

        self.assertFalse(failing.deltatech_image_optimized)
        self.assertTrue((variants - failing).deltatech_image_optimized, "the next variant is still processed")

    def test_attachment_stored_in_database_is_not_shared(self):
        att = self.env["ir.attachment"].create({"name": "link", "type": "url", "url": "https://example.com/a.png"})
        self.assertFalse(att.store_fname)
        self.assertFalse(att._dt_image_shared_file())
