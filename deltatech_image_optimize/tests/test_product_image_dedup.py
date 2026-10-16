# ©  2026 Terrabit
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import io

from PIL import Image

from odoo.tests import TransactionCase, tagged


def make_image(color):
    """Un PNG minimal de culoare dată — două culori diferite = două checksum-uri."""
    buffer = io.BytesIO()
    Image.new("RGB", (16, 16), color).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


@tagged("post_install", "-at_install")
class TestProductImageDedup(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.red = make_image((255, 0, 0))
        cls.blue = make_image((0, 0, 255))
        cls.product_a = cls.env["product.template"].create({"name": "Dedup Product A", "type": "consu"})
        cls.product_b = cls.env["product.template"].create({"name": "Dedup Product B", "type": "consu"})

    def create_image(self, name, product, data, sequence=10):
        return self.env["product.image"].create(
            {
                "name": name,
                "product_tmpl_id": product.id,
                "image_1920": data,
                "sequence": sequence,
            }
        )

    def test_checksum_is_computed_from_attachment(self):
        """Aceeași imagine dă același checksum; una diferită dă altul."""
        first = self.create_image("red 1", self.product_a, self.red)
        second = self.create_image("red 2", self.product_a, self.red)
        other = self.create_image("blue", self.product_a, self.blue)

        self.assertTrue(first.image_checksum)
        self.assertEqual(first.image_checksum, second.image_checksum)
        self.assertNotEqual(first.image_checksum, other.image_checksum)

    def test_checksum_matches_the_attachment_odoo_wrote(self):
        """Valoarea trebuie să fie cea din ir.attachment, altfel nu e comparabilă."""
        image = self.create_image("red", self.product_a, self.red)
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "product.image"),
                    ("res_field", "=", "image_1920"),
                    ("res_id", "=", image.id),
                ]
            )
        )
        self.assertEqual(len(attachment), 1)
        self.assertEqual(image.image_checksum, attachment.checksum)

    def test_duplicates_inside_one_product_are_removable(self):
        first = self.create_image("red 1", self.product_a, self.red, sequence=1)
        second = self.create_image("red 2", self.product_a, self.red, sequence=2)
        third = self.create_image("red 3", self.product_a, self.red, sequence=3)

        wizard = self.env["deltatech.product.image.dedup"].create({})
        to_remove = wizard._images_to_remove([first.image_checksum])

        self.assertEqual(to_remove, second | third, "trebuie păstrată prima după sequence")

        wizard.checksums = first.image_checksum
        wizard.action_apply()

        self.assertTrue(first.exists())
        self.assertFalse(second.exists())
        self.assertFalse(third.exists())
        self.assertEqual(wizard.removed_count, 2)

    def test_same_image_on_different_products_is_never_removed(self):
        """Fiecare produs are nevoie de exemplarul lui — altfel rămâne fără poză."""
        on_a = self.create_image("red", self.product_a, self.red)
        on_b = self.create_image("red", self.product_b, self.red)

        wizard = self.env["deltatech.product.image.dedup"].create({})
        to_remove = wizard._images_to_remove([on_a.image_checksum])

        self.assertFalse(to_remove)
        self.assertTrue(on_a.exists())
        self.assertTrue(on_b.exists())

    def test_video_records_are_kept(self):
        """Un product.image cu video nu se șterge: videoul nu e duplicat."""
        self.create_image("red 1", self.product_a, self.red, sequence=1)
        with_video = self.create_image("red 2", self.product_a, self.red, sequence=2)
        with_video.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

        wizard = self.env["deltatech.product.image.dedup"].create({})
        self.assertNotIn(with_video, wizard._images_to_remove([with_video.image_checksum]))

    def test_report_counts_copies_and_products(self):
        self.create_image("red 1", self.product_a, self.red)
        self.create_image("red 2", self.product_a, self.red)
        self.create_image("red 3", self.product_b, self.red)
        checksum = (
            self.env["product.image"].search([("product_tmpl_id", "=", self.product_a.id)], limit=1).image_checksum
        )

        self.env.flush_all()
        group = self.env["deltatech.product.image.duplicate"].search([("image_checksum", "=", checksum)])
        self.assertEqual(len(group), 1)
        self.assertEqual(group.image_count, 3)
        self.assertEqual(group.product_count, 2)
        self.assertEqual(group.removable_count, 1)

    def test_report_list_loads_in_the_web_client(self):
        """Lista citește și write_date (widget-ul de imagine); vederea SQL trebuie să-l aibă."""
        self.create_image("red 1", self.product_a, self.red)
        self.create_image("red 2", self.product_a, self.red)
        self.env.flush_all()

        spec = {name: {} for name in ("sample_image", "image_count", "product_names", "write_date")}
        result = self.env["deltatech.product.image.duplicate"].web_search_read([], spec)
        self.assertTrue(result["records"])
        self.assertTrue(result["records"][0]["write_date"])

    def test_backfill_fills_missing_checksums(self):
        image = self.create_image("red", self.product_a, self.red)
        expected = image.image_checksum

        # simulăm starea de dinainte de instalare
        self.env.flush_all()
        self.env.cr.execute("UPDATE product_image SET image_checksum = NULL WHERE id = %s", (image.id,))
        self.env.invalidate_all(flush=False)
        self.assertFalse(image.image_checksum)

        updated = self.env["product.image"]._dedup_backfill_checksums()

        self.assertGreaterEqual(updated, 1)
        self.assertEqual(image.image_checksum, expected)

    def test_binary_fallback_does_not_prefetch_siblings(self):
        """Fallback-ul pe binar nu are voie să încarce imaginile fraților.

        Regresia care a omorât instalarea pe un catalog de ~70.000 imagini:
        citirea unui câmp binary pe un record dintr-un recordset mare
        prefetch-uiește imaginile tuturor fraților în cache.
        """
        first = self.create_image("red", self.product_a, self.red)
        second = self.create_image("blue", self.product_a, self.blue)
        images = first | second
        field = self.env["product.image"]._fields["image_1920"]

        self.env.invalidate_all()
        self.assertTrue(images[0]._dedup_checksum_from_binary())

        self.assertFalse(
            images[1].id in field._get_cache(self.env),
            "citirea imaginii unui record a prefetch-uit si fratii",
        )

    def test_pre_init_hook_fills_the_column(self):
        """Hook-ul de pre-init populează coloana înainte ca ORM-ul să vadă câmpul."""
        from odoo.addons.deltatech_image_optimize.hooks import pre_init_hook

        image = self.create_image("red", self.product_a, self.red)
        expected = image.image_checksum

        self.env.flush_all()
        self.env.cr.execute("UPDATE product_image SET image_checksum = NULL WHERE id = %s", (image.id,))
        self.env.invalidate_all(flush=False)
        self.assertFalse(image.image_checksum)

        pre_init_hook(self.env)

        self.env.invalidate_all(flush=False)
        self.assertEqual(image.image_checksum, expected)

    def test_checksum_of_an_unsaved_image(self):
        """Un record nou n-are atașament: checksum-ul vine din imaginea însăși."""
        image = self.env["product.image"].new({"name": "draft", "image_1920": self.red})
        saved = self.create_image("red", self.product_a, self.red)
        self.assertEqual(image.image_checksum, saved.image_checksum)
        self.assertFalse(self.env["product.image"].new({"name": "empty"})._dedup_checksum_from_binary())

    def test_duplicate_count_and_view_copies(self):
        first = self.create_image("red 1", self.product_a, self.red)
        self.create_image("red 2", self.product_b, self.red)
        single = self.create_image("blue", self.product_a, self.blue)

        self.assertEqual(first.duplicate_count, 2)
        self.assertEqual(single.duplicate_count, 1)
        action = first.action_view_duplicates()
        self.assertEqual(action["res_model"], "product.image")
        self.assertEqual(action["domain"], [("image_checksum", "=", first.image_checksum)])

    def test_report_actions(self):
        first = self.create_image("red 1", self.product_a, self.red)
        self.create_image("red 2", self.product_a, self.red)
        self.env.flush_all()
        group = self.env["deltatech.product.image.duplicate"].search([("image_checksum", "=", first.image_checksum)])

        images = self.env["product.image"].search(group.action_view_images()["domain"])
        self.assertEqual(len(images), 2)
        context = group.action_clean()["context"]
        self.assertEqual(context, {"active_model": group._name, "active_ids": group.ids})

    def test_wizard_works_only_on_the_selected_groups(self):
        self.create_image("red 1", self.product_a, self.red)
        red_copy = self.create_image("red 2", self.product_a, self.red, sequence=20)
        self.create_image("blue 1", self.product_b, self.blue)
        blue_copy = self.create_image("blue 2", self.product_b, self.blue, sequence=20)
        self.env.flush_all()
        red_group = self.env["deltatech.product.image.duplicate"].search(
            [("image_checksum", "=", red_copy.image_checksum)]
        )

        action = red_group.action_clean()
        wizard = self.env[action["res_model"]].with_context(**action["context"]).create({})
        self.assertEqual(wizard.checksums, red_copy.image_checksum)
        self.assertEqual(wizard.removable_count, 1)
        self.assertEqual(wizard.kept_count, 1)
        wizard.action_apply()

        self.assertEqual(wizard.removed_count, 1)
        self.assertFalse(red_copy.exists())
        self.assertTrue(blue_copy.exists(), "a group that was not selected is left alone")

    def test_counts_without_checksums_and_long_preview(self):
        Dedup = self.env["deltatech.product.image.dedup"]
        self.assertEqual(Dedup._kept_count([]), 0)
        self.assertFalse(Dedup._images_to_remove([]))

        first = self.create_image("red 1", self.product_a, self.red)
        second = self.create_image("red 2", self.product_b, self.red)
        self.assertEqual(Dedup._kept_count([first.image_checksum]), 2)

        preview = Dedup._build_preview(first | second, limit=1).splitlines()
        self.assertEqual(len(preview), 2)
        self.assertIn(f"(#{first.id})", preview[0])
        self.assertIn("1 more", preview[1])

    def test_same_image_on_different_attribute_values_is_kept(self):
        """Odoo 20: imaginile unei variante sunt pe șablon, legate prin valorile de atribut."""
        attribute = self.env["product.attribute"].create(
            {
                "name": "Dedup Color",
                "value_ids": [(0, 0, {"name": "Red"}), (0, 0, {"name": "Blue"})],
            }
        )
        template = self.env["product.template"].create(
            {
                "name": "Dedup Variants",
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, attribute.value_ids.ids)]})
                ],
            }
        )
        ptav_red, ptav_blue = template.attribute_line_ids.product_template_value_ids
        on_red = self.create_image("red", template, self.red, sequence=1)
        on_red.attribute_value_ids = ptav_red
        on_blue = self.create_image("red", template, self.red, sequence=2)
        on_blue.attribute_value_ids = ptav_blue
        copy_red = self.create_image("red copy", template, self.red, sequence=3)
        copy_red.attribute_value_ids = ptav_red

        Dedup = self.env["deltatech.product.image.dedup"]
        self.assertEqual(Dedup._images_to_remove([on_red.image_checksum]), copy_red)
        self.assertEqual(Dedup._kept_count([on_red.image_checksum]), 2)
        self.assertIn("(Red)", Dedup._build_preview(copy_red))

        self.env.flush_all()
        group = self.env["deltatech.product.image.duplicate"].search([("image_checksum", "=", on_red.image_checksum)])
        self.assertEqual(group.image_count, 3)
        self.assertEqual(group.product_count, 2)
        self.assertEqual(group.removable_count, 1)
