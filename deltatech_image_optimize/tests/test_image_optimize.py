import base64
import io
import os

from odoo.tests import TransactionCase, tagged

try:
    from PIL import Image
except ImportError:
    Image = None


@tagged("post_install", "-at_install")
class TestImageOptimize(TransactionCase):
    def _make_big_jpeg(self, size=2200):
        """Build a noisy JPEG that is large and above the 1920 limit."""
        raw = os.urandom(size * size * 3)
        img = Image.frombytes("RGB", (size, size), raw)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95)
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

        self.env["res.partner"].create({"name": "Image Optimize Test 2", "image_1920": self._make_big_jpeg()})
        self.env["ir.attachment"]._dt_image_optimize_run(limit=50)
        # Everything processed is flagged, so a second run finds nothing new.
        stats = self.env["ir.attachment"]._dt_image_optimize_run(limit=50)
        self.assertEqual(stats["optimized"], 0)
