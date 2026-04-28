from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestMrpProductionBom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Base Product",
                "is_storable": True,
            }
        )
        # Odoo creează automat o variantă când creăm template-ul.
        cls.product_variant = cls.product_tmpl.product_variant_id
        cls.component = cls.env["product.product"].create(
            {
                "name": "Component",
                "is_storable": True,
            }
        )
        cls.base_bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_tmpl.id,
                "base_type": "base",
                "bom_line_ids": [(0, 0, {"product_id": cls.component.id, "product_qty": 1.0})],
            }
        )

    def test_action_compute_derived_bom_twice(self):
        production = self.env["mrp.production"].create(
            {
                "product_id": self.product_variant.id,
                "product_uom_id": self.product_tmpl.uom_id.id,
                "bom_id": self.base_bom.id,
            }
        )
        production._compute_move_raw_ids()
        num_moves_initial = len(production.move_raw_ids)

        # Prima apăsare
        production.action_compute_derived_bom()
        production._compute_move_raw_ids()
        num_moves_1 = len(production.move_raw_ids)

        # A doua apăsare
        production.action_compute_derived_bom()
        production._compute_move_raw_ids()
        num_moves_2 = len(production.move_raw_ids)

        self.assertEqual(
            num_moves_1,
            num_moves_initial,
            "Numărul de linii nu ar trebui să se schimbe după prima calculare dacă structura e aceeași",
        )
        self.assertEqual(num_moves_2, num_moves_1, "Numărul de linii s-a dublat după a doua apăsare a butonului!")

    def test_derived_bom_reference(self):
        # Primul BoM derivat pentru acest template
        production1 = self.env["mrp.production"].create(
            {
                "product_id": self.product_variant.id,
                "product_uom_id": self.product_tmpl.uom_id.id,
                "bom_id": self.base_bom.id,
            }
        )
        production1.action_compute_derived_bom()
        self.assertEqual(production1.bom_id.code, "D1")

        # Al doilea BoM derivat pentru același template, dar alt produs (variantă)
        # Creăm o altă variantă
        attr_color = self.env["product.attribute"].create({"name": "Color"})
        attr_val_red = self.env["product.attribute.value"].create({"name": "Red", "attribute_id": attr_color.id})
        attr_val_blue = self.env["product.attribute.value"].create({"name": "Blue", "attribute_id": attr_color.id})

        product_tmpl_v2 = self.env["product.template"].create(
            {
                "name": "Product V2",
                "is_storable": True,
                "attribute_line_ids": [
                    (0, 0, {"attribute_id": attr_color.id, "value_ids": [(6, 0, [attr_val_red.id, attr_val_blue.id])]})
                ],
            }
        )
        base_bom_v2 = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": product_tmpl_v2.id,
                "base_type": "base",
                "bom_line_ids": [(0, 0, {"product_id": self.component.id, "product_qty": 1.0})],
            }
        )

        variant_red = product_tmpl_v2.product_variant_ids.filtered(
            lambda v: attr_val_red in v.product_template_attribute_value_ids.product_attribute_value_id
        )
        variant_blue = product_tmpl_v2.product_variant_ids.filtered(
            lambda v: attr_val_blue in v.product_template_attribute_value_ids.product_attribute_value_id
        )

        prod_red = self.env["mrp.production"].create(
            {
                "product_id": variant_red.id,
                "bom_id": base_bom_v2.id,
            }
        )
        prod_red.action_compute_derived_bom()
        self.assertEqual(prod_red.bom_id.code, "D1")

        prod_blue = self.env["mrp.production"].create(
            {
                "product_id": variant_blue.id,
                "bom_id": base_bom_v2.id,
            }
        )
        prod_blue.action_compute_derived_bom()
        self.assertEqual(prod_blue.bom_id.code, "D2")
