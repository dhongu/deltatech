# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestProductAttributeRole(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # the base module defines no roles: add one for the test, as a module
        # using the field would with `selection_add`
        field = cls.env["product.attribute"]._fields["attribute_role"]
        selection = [*field.selection, ("variety", "Variety")]
        cls.startClassPatcher(patch.object(field, "selection", selection))
        cls.startClassPatcher(patch.object(field, "_selection", dict(selection)))

        Attribute = cls.env["product.attribute"]
        Attribute.search([("attribute_role", "=", "variety")]).attribute_role = False
        cls.variety = Attribute.create(
            {
                "name": "Soi",
                "create_variant": "always",
                "attribute_role": "variety",
                "value_ids": [(0, 0, {"name": "Gala"}), (0, 0, {"name": "Idared"})],
            }
        )
        cls.size = Attribute.create(
            {
                "name": "Size",
                "create_variant": "always",
                "value_ids": [(0, 0, {"name": "70/75 mm"})],
            }
        )
        cls.template = cls.env["product.template"].create(
            {
                "name": "Apples",
                "attribute_line_ids": [
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.variety.id,
                            "value_ids": [(6, 0, cls.variety.value_ids.ids)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "attribute_id": cls.size.id,
                            "value_ids": [(6, 0, cls.size.value_ids.ids)],
                        },
                    ),
                ],
            }
        )

    def test_value_by_role(self):
        gala = self.variety.value_ids.filtered(lambda v: v.name == "Gala")
        variant = self.template.product_variant_ids.filtered(
            lambda p: gala in p.product_template_attribute_value_ids.mapped("product_attribute_value_id")
        )
        self.assertEqual(variant._get_attribute_value_by_role("variety"), gala)
        self.assertFalse(variant._get_attribute_value_by_role("grade"))
        self.assertFalse(self.env["product.product"]._get_attribute_value_by_role("variety"))

    def test_role_survives_rename(self):
        self.variety.with_context(lang="en_US").name = "Variety"
        Attribute = self.env["product.attribute"]
        self.assertEqual(Attribute._get_attribute_by_role("variety"), self.variety)
        variant = self.template.product_variant_ids[:1]
        self.assertTrue(variant._get_attribute_value_by_role("variety"))

    def test_archived_attribute_is_found(self):
        self.variety.active = False
        self.assertEqual(
            self.env["product.attribute"]._get_attribute_by_role("variety"),
            self.variety,
        )

    def test_role_is_unique(self):
        with (
            self.assertRaises(IntegrityError),
            mute_logger("odoo.sql_db"),
            self.env.cr.savepoint(),
        ):
            self.size.attribute_role = "variety"
            self.size.flush_recordset()
