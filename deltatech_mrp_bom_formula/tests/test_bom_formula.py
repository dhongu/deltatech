# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBomFormula(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.ref("base.group_user").write(
            {"implied_ids": [Command.link(cls.env.ref("product.group_product_variant").id)]}
        )

        cls.attr_finish = cls.env["product.attribute"].create(
            {
                "name": "Finish",
                "create_variant": "always",
                "value_ids": [
                    Command.create({"name": "Galvanized"}),
                    Command.create({"name": "Painted"}),
                ],
            }
        )
        cls.attr_width = cls.env["product.attribute"].create(
            {
                "name": "Width",
                "create_variant": "always",
                "value_ids": [
                    Command.create({"name": "1000 mm", "numeric_value": 1000.0}),
                    Command.create({"name": "1250 mm", "numeric_value": 1250.0}),
                ],
            }
        )

        cls.template = cls.env["product.template"].create(
            {
                "name": "Configured Panel",
                "is_storable": True,
                "attribute_line_ids": [
                    Command.create(
                        {
                            "attribute_id": cls.attr_finish.id,
                            "value_ids": [Command.set(cls.attr_finish.value_ids.ids)],
                        }
                    ),
                    Command.create(
                        {
                            "attribute_id": cls.attr_width.id,
                            "value_ids": [Command.set(cls.attr_width.value_ids.ids)],
                        }
                    ),
                ],
            }
        )
        cls.sheet = cls.env["product.product"].create({"name": "Steel Sheet", "is_storable": True})
        cls.zinc = cls.env["product.product"].create({"name": "Zinc", "is_storable": True})

        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.template.id,
                "product_qty": 1.0,
                "type": "normal",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.sheet.id,
                            "product_qty": 1.0,
                            "qty_formula": "num['width'] / 1000",
                        }
                    ),
                    Command.create(
                        {
                            "product_id": cls.zinc.id,
                            "product_qty": 1.0,
                            "qty_formula": "0.8 if attr['finish'] == 'galvanized' else 0.1",
                        }
                    ),
                ],
            }
        )

    def _get_variant(self, finish, width):
        finish_value = self.attr_finish.value_ids.filtered(lambda v, n=finish: v.name == n)
        width_value = self.attr_width.value_ids.filtered(lambda v, n=width: v.name == n)
        ptav = self.template.attribute_line_ids.product_template_value_ids.filtered(
            lambda v, f=finish_value, w=width_value: v.product_attribute_value_id in (f | w)
        )
        return self.template._get_variant_for_combination(ptav)

    def _exploded_quantities(self, variant, quantity=1.0):
        _boms, lines = self.bom.explode(variant, quantity)
        return {line.product_id: values["qty"] for line, values in lines}

    def test_attribute_codes_are_generated(self):
        self.assertEqual(self.attr_finish.code, "finish")
        self.assertEqual(self.attr_width.code, "width")
        galvanized = self.attr_finish.value_ids.filtered(lambda v: v.name == "Galvanized")
        self.assertEqual(galvanized.code, "galvanized")

    def test_duplicate_attribute_code_is_suffixed(self):
        other = self.env["product.attribute"].create({"name": "Finish"})
        self.assertEqual(other.code, "finish_2")

    def test_numeric_formula(self):
        quantities = self._exploded_quantities(self._get_variant("Galvanized", "1250 mm"))
        self.assertAlmostEqual(quantities[self.sheet], 1.25)

    def test_discrete_formula(self):
        galvanized = self._exploded_quantities(self._get_variant("Galvanized", "1000 mm"))
        painted = self._exploded_quantities(self._get_variant("Painted", "1000 mm"))
        self.assertAlmostEqual(galvanized[self.zinc], 0.8)
        self.assertAlmostEqual(painted[self.zinc], 0.1)

    def test_formula_scales_with_produced_quantity(self):
        quantities = self._exploded_quantities(self._get_variant("Galvanized", "1250 mm"), quantity=4.0)
        self.assertAlmostEqual(quantities[self.sheet], 5.0)

    def test_line_without_formula_keeps_its_quantity(self):
        self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.sheet).qty_formula = False
        quantities = self._exploded_quantities(self._get_variant("Galvanized", "1250 mm"))
        self.assertAlmostEqual(quantities[self.sheet], 1.0)

    def test_formula_uses_line_quantity(self):
        line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.sheet)
        line.write({"product_qty": 3.0, "qty_formula": "qty * num['width'] / 1000"})
        quantities = self._exploded_quantities(self._get_variant("Painted", "1000 mm"))
        self.assertAlmostEqual(quantities[self.sheet], 3.0)

    def test_unknown_attribute_code_is_rejected_on_save(self):
        line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.zinc)
        with self.assertRaises(ValidationError):
            line.qty_formula = "num['thickness'] * 2"

    def test_syntax_error_is_rejected_on_save(self):
        line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.zinc)
        with self.assertRaises(ValidationError):
            line.qty_formula = "num['width'] *"

    def test_negative_quantity_is_rejected(self):
        line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.zinc)
        with self.assertRaises(ValidationError):
            line.qty_formula = "-1"

    def test_non_numeric_result_is_rejected(self):
        line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.zinc)
        with self.assertRaises(ValidationError):
            line.qty_formula = "attr['finish']"

    def test_formula_cannot_reach_the_environment(self):
        line = self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.zinc)
        with self.assertRaises(ValidationError):
            line.qty_formula = "self.env['res.users'].search([])"

    def test_nested_bom_uses_the_root_configuration(self):
        semi_finished = self.env["product.product"].create({"name": "Frame", "is_storable": True})
        self.env["mrp.bom"].create(
            {
                "product_tmpl_id": semi_finished.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "phantom",
                "bom_line_ids": [
                    Command.create(
                        {
                            "product_id": self.zinc.id,
                            "product_qty": 1.0,
                            "qty_formula": "num['width'] / 500",
                        }
                    )
                ],
            }
        )
        self.bom.bom_line_ids.filtered(lambda line: line.product_id == self.zinc).unlink()
        self.env["mrp.bom.line"].create(
            {
                "bom_id": self.bom.id,
                "product_id": semi_finished.id,
                "product_qty": 1.0,
            }
        )
        quantities = self._exploded_quantities(self._get_variant("Galvanized", "1250 mm"))
        # The kit line carries no formula, the nested line reads the width of the root variant.
        self.assertAlmostEqual(quantities[self.zinc], 2.5)
