import base64
import io
import logging
import re

from odoo.tests import HttpCase, JsonRpcException, new_test_user, tagged

from odoo.addons.deltatech_image_optimize.models.ir_attachment import Image, _webp_available
from odoo.addons.web.tests.test_js import unit_test_error_checker

BG_COLOR = (120, 200, 120)
PRODUCT_COLOR = (90, 90, 95)

# hoot raportează succes și când filtrul nu prinde niciun test
MIN_HOOT_TESTS = 3
RE_PASSED = re.compile(r"Passed (\d+) tests")


def _picture(size=(400, 300)):
    """O fotografie de produs pe fundal uniform: decupajul prin culoare, fără rembg."""
    img = Image.new("RGB", size, BG_COLOR)
    img.paste(Image.new("RGB", (size[0] // 2, size[1] // 6), PRODUCT_COLOR), (size[0] // 8, size[1] // 3))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@tagged("post_install", "-at_install")
class TestImageBackgroundEditor(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.image = _picture()
        cls.template = cls.env["product.template"].create(
            {"name": "BG Editor Product", "image_1920": cls.image, "is_published": True, "website_id": False}
        )
        cls.gallery = cls.env["product.image"].create(
            {"name": "BG Editor Gallery", "image_1920": cls.image, "product_tmpl_id": cls.template.id}
        )

    def _call(self, route, model, res_id, **params):
        return self.make_jsonrpc_request(
            f"/deltatech_image_optimize/bg/{route}", {"model": model, "res_id": res_id, **params}
        )

    def _alpha(self, record, field="image_1920", xy=(5, 5)):
        _webp_available()
        return Image.open(io.BytesIO(record[field].content)).convert("RGBA").getpixel(xy)[3]

    def test_preview_writes_nothing(self):
        self.authenticate("admin", "admin")
        result = self._call("preview", "product.template", self.template.id)
        self.assertEqual(result["method"], "auto")
        self.assertTrue(result["before"])
        self.assertTrue(result["after"])
        self.assertFalse(result["warning"])
        self.template.invalidate_recordset()
        self.assertEqual(self.template.image_1920.to_base64(), self.image, "the preview writes nothing")
        self.assertFalse(self.template.bg_removal_state)

    def test_apply_template_and_gallery(self):
        self.authenticate("admin", "admin")
        self.assertTrue(self._call("apply", "product.template", self.template.id, method="uniform"))
        self.assertTrue(self._call("apply", "product.image", self.gallery.id))
        for record in (self.template, self.gallery):
            record.invalidate_recordset()
            self.assertEqual(record.bg_removal_state, "done")
            self.assertEqual(self._alpha(record), 0, "the background is transparent")
            self.assertEqual(self._alpha(record, xy=(150, 110)), 255, "the product stays opaque")

    def test_variant_without_own_picture_writes_template(self):
        self.authenticate("admin", "admin")
        variant = self.template.product_variant_id
        self.assertFalse(variant.image_variant_1920)
        self._call("apply", "product.product", variant.id)
        self.template.invalidate_recordset()
        variant.invalidate_recordset()
        self.assertEqual(self.template.bg_removal_state, "done")
        self.assertFalse(variant.image_variant_1920, "the variant still shows the picture of the template")

    def test_variant_with_own_picture(self):
        self.authenticate("admin", "admin")
        variant = self.template.product_variant_id
        variant.image_variant_1920 = _picture((300, 300))
        self._call("apply", "product.product", variant.id)
        variant.invalidate_recordset()
        self.template.invalidate_recordset()
        self.assertEqual(variant.bg_removal_state, "done")
        self.assertEqual(self._alpha(variant, "image_variant_1920"), 0)
        self.assertEqual(self.template.image_1920.to_base64(), self.image, "the template picture is not touched")
        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "product.product"),
                ("res_id", "=", variant.id),
                ("res_field", "like", "image_variant_%"),
            ]
        )
        self.assertTrue(attachments)
        self.assertTrue(all(att.deltatech_image_optimized for att in attachments), "the resized variants are recoded")

    def test_refused_on_other_models(self):
        self.authenticate("admin", "admin")
        partner = self.env["res.partner"].create({"name": "BG partner", "image_1920": self.image})
        with self.assertRaises(JsonRpcException), self.assertLogs("odoo.http", level=logging.WARNING):
            self._call("preview", "res.partner", partner.id)

    def test_refused_without_write_access(self):
        new_test_user(self.env, login="bg_employee", groups="base.group_user")
        self.authenticate("bg_employee", "bg_employee")
        with self.assertRaises(JsonRpcException), self.assertLogs("odoo.http", level=logging.WARNING):
            self._call("apply", "product.template", self.template.id)
        self.template.invalidate_recordset()
        self.assertEqual(self.template.image_1920.to_base64(), self.image)

    def test_editor_tour(self):
        self.start_tour(
            self.env["website"].get_client_action_url(self.template.website_url),
            "deltatech_image_optimize_remove_background_editor",
            login="admin",
        )
        self.template.invalidate_recordset()
        self.assertEqual(self.template.bg_removal_state, "done")
        self.assertEqual(self._alpha(self.template), 0)

    def test_hoot(self):
        collected = []

        class _Collector(logging.Handler):
            def emit(self, record):
                match = RE_PASSED.search(record.getMessage())
                if match:
                    collected.append(int(match.group(1)))

        browser_logger = logging.getLogger(__name__)
        handler = _Collector()
        browser_logger.addHandler(handler)
        self.addCleanup(browser_logger.removeHandler, handler)
        self.browser_js(
            "/web/tests?headless&loglevel=2&preset=desktop&timeout=15000&filter=%22deltatech_image_optimize%22",
            "",
            "",
            login="admin",
            timeout=300,
            success_signal="[HOOT] Test suite succeeded",
            error_checker=unit_test_error_checker,
        )
        self.assertTrue(collected, "hoot did not report how many tests it ran")
        self.assertGreaterEqual(collected[0], MIN_HOOT_TESTS, f"hoot ran {collected[0]} tests")
