# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.stock_account.tests.common import TestStockValuationCommon


@tagged("post_install", "-at_install")
class TestStockDisassemblyBom(TestStockValuationCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        def product(name, **vals):
            return cls.env["product.product"].create(
                {**cls.product_common_vals, "name": name, "categ_id": cls.category_avco_auto.id, **vals}
            )

        cls.part_a = product("Part A")
        cls.part_b = product("Part B")
        cls.service = cls.env["product.product"].create({"name": "Labour", "type": "service"})
        cls.kit = product("Kit", is_storable=False, type="consu")
        cls.kit_part = product("Kit part")
        cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.kit.product_tmpl_id.id,
                "type": "phantom",
                "bom_line_ids": [(0, 0, {"product_id": cls.kit_part.id, "product_qty": 3})],
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.product_avco_auto.product_tmpl_id.id,
                "product_qty": 2,
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.part_a.id, "product_qty": 2}),
                    (0, 0, {"product_id": cls.part_b.id, "product_qty": 6}),
                    (0, 0, {"product_id": cls.service.id, "product_qty": 1}),
                    (0, 0, {"product_id": cls.kit.id, "product_qty": 1}),
                ],
            }
        )

    def test_load_bom(self):
        self._make_in_move(self.product_avco_auto, 10, unit_cost=10)
        disassembly = self.env["stock.disassembly"].create(
            {
                "product_id": self.product_avco_auto.id,
                "product_qty": 3,
                "location_id": self.stock_location.id,
                "allocation_method": "quantity",
                "line_ids": [
                    (0, 0, {"product_id": self.part_b.id, "quantity": 99}),
                    (0, 0, {"product_id": self.part_b.id, "quantity": 1, "line_type": "scrap"}),
                ],
            }
        )
        self.assertEqual(disassembly.bom_id, self.bom)
        disassembly.action_load_bom()

        products = disassembly.line_ids.filtered(lambda line: line.line_type == "product")
        # the BoM is for 2 units: 3 units give 1.5 times its lines; the kit gives its part, the service nothing
        self.assertEqual(products.product_id, self.part_a | self.part_b | self.kit_part)
        self.assertEqual(products.mapped("quantity"), [3, 9, 4.5])
        # the loss line is kept
        self.assertEqual(len(disassembly.line_ids.filtered(lambda line: line.line_type == "scrap")), 1)

        disassembly.action_validate()
        self.assertEqual(disassembly.state, "done")
        self.assertAlmostEqual(sum(products.move_ids.mapped("value")), 30)
