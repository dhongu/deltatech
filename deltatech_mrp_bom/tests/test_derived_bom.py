from odoo import Command
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestDerivedBom(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attr_color = cls.env["product.attribute"].create({"name": "Color", "create_variant": "always"})
        cls.val_red = cls.env["product.attribute.value"].create({"name": "Red", "attribute_id": cls.attr_color.id})
        cls.val_blue = cls.env["product.attribute.value"].create({"name": "Blue", "attribute_id": cls.attr_color.id})
        color_line = [
            Command.create(
                {"attribute_id": cls.attr_color.id, "value_ids": [Command.set([cls.val_red.id, cls.val_blue.id])]}
            )
        ]
        cls.finished_tmpl = cls.env["product.template"].create(
            {"name": "Chair", "is_storable": True, "attribute_line_ids": color_line}
        )
        cls.paint_tmpl = cls.env["product.template"].create(
            {"name": "Paint", "is_storable": True, "attribute_line_ids": color_line}
        )
        cls.screw = cls.env["product.product"].create({"name": "Screw", "is_storable": True})

        cls.chair_red = cls._variant(cls.finished_tmpl, cls.val_red)
        cls.chair_blue = cls._variant(cls.finished_tmpl, cls.val_blue)
        cls.paint_red = cls._variant(cls.paint_tmpl, cls.val_red)
        cls.paint_blue = cls._variant(cls.paint_tmpl, cls.val_blue)

        cls.base_bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_tmpl.id,
                "base_type": "base",
                "bom_line_ids": [
                    Command.create({"product_id": cls.paint_red.id, "product_qty": 2.0}),
                    Command.create({"product_id": cls.screw.id, "product_qty": 4.0}),
                ],
            }
        )

    @classmethod
    def _variant(cls, tmpl, value):
        return tmpl.product_variant_ids.filtered(
            lambda p: value in p.product_template_attribute_value_ids.product_attribute_value_id
        )

    def _derived_bom(self, product):
        return self.env["mrp.bom"].search([("product_id", "=", product.id), ("base_type", "=", "derived")])

    def test_recompute_from_base_maps_attribute_variants(self):
        derived = self.env["mrp.bom"].create(
            {"product_tmpl_id": self.finished_tmpl.id, "product_id": self.chair_blue.id, "base_type": "derived"}
        )
        derived.recompute_from_base()
        self.assertEqual(derived.bom_line_ids.product_id, self.paint_blue | self.screw)
        paint_line = derived.bom_line_ids.filtered(lambda line: line.product_id == self.paint_blue)
        self.assertEqual(paint_line.product_qty, 2.0)
        # baza rămâne neatinsă
        self.assertEqual(self.base_bom.bom_line_ids.product_id, self.paint_red | self.screw)

        # recalcularea repetată nu dublează liniile
        derived.recompute_from_base()
        self.assertEqual(len(derived.bom_line_ids), 2)

    def test_recompute_from_base_ignores_non_derived(self):
        self.base_bom.recompute_from_base()
        self.assertEqual(len(self.base_bom.bom_line_ids), 2)

    def test_production_confirm_switches_to_derived_bom(self):
        production = self.env["mrp.production"].create(
            {"product_id": self.chair_blue.id, "bom_id": self.base_bom.id, "product_qty": 1.0}
        )
        production.action_confirm()
        derived = self._derived_bom(self.chair_blue)
        self.assertTrue(derived)
        self.assertEqual(production.bom_id, derived)
        self.assertEqual(production.bom_base_type, "derived")
        self.assertEqual(production.state, "confirmed")
        self.assertEqual(production.move_raw_ids.product_id, self.paint_blue | self.screw)

    def test_report_bom_structure_uses_derived_bom(self):
        report = self.env["report.mrp.report_bom_structure"]
        res = report.get_html(bom_id=self.base_bom.id, searchQty=1, searchVariant=self.chair_red.id)
        derived = self._derived_bom(self.chair_red)
        self.assertTrue(derived)
        self.assertEqual(res["lines"]["bom_id"], derived.id)
        self.assertEqual(derived.bom_line_ids.product_id, self.paint_red | self.screw)

    def test_open_bom_on_line_with_child_bom(self):
        paint_bom = self.env["mrp.bom"].create(
            {
                "product_tmpl_id": self.paint_tmpl.id,
                "bom_line_ids": [Command.create({"product_id": self.screw.id, "product_qty": 1.0})],
            }
        )
        line = self.base_bom.bom_line_ids.filtered(lambda bom_line: bom_line.product_id == self.paint_red)
        self.assertEqual(line.child_bom_id, paint_bom)
        action = line.open_bom()
        self.assertEqual(action["res_model"], "mrp.bom")
        self.assertEqual(action["res_id"], paint_bom.id)

    def test_onchange_product_tmpl_sets_bom_uom(self):
        uom_dozen = self.env.ref("uom.product_uom_dozen")
        bom = self.env["mrp.bom"].new({"product_tmpl_id": self.finished_tmpl.id, "uom_id": uom_dozen.id})
        bom.onchange_product_tmpl_id()
        self.assertEqual(bom.uom_id, self.finished_tmpl.uom_id)
