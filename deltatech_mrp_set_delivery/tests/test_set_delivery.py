# © 2025 Deltatech
# See README.rst file on the addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestSetDelivery(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Customer"})
        cls.stock_location = cls.env.ref("stock.stock_location_stock")
        cls.kit = cls.env["product.product"].create({"name": "Kit", "type": "consu"})
        cls.comp_1 = cls.env["product.product"].create({"name": "Comp 1", "type": "consu", "is_storable": True})
        cls.comp_2 = cls.env["product.product"].create({"name": "Comp 2", "type": "consu", "is_storable": True})
        for comp in cls.comp_1 | cls.comp_2:
            cls.env["stock.quant"]._update_available_quantity(comp, cls.stock_location, 100)
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.kit.product_tmpl_id.id,
                "product_qty": 1.0,
                "type": "phantom",
                "restrict_incomplete_delivery": True,
                "bom_line_ids": [
                    (0, 0, {"product_id": cls.comp_1.id, "product_qty": 1}),
                    (0, 0, {"product_id": cls.comp_2.id, "product_qty": 2}),
                ],
            }
        )

    def _confirm_sale(self, qty=2):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.kit.id, "product_uom_qty": qty})],
            }
        )
        order.action_confirm()
        picking = order.picking_ids
        self.assertEqual(len(picking.move_ids), 2)
        return picking

    def _set_quantities(self, picking, qty_1, qty_2):
        for move in picking.move_ids:
            move.quantity = qty_1 if move.product_id == self.comp_1 else qty_2
            move.picked = True

    def test_complete_set(self):
        picking = self._confirm_sale()
        self._set_quantities(picking, 2, 4)
        self.assertFalse(picking.check_complete_set())
        picking.button_validate()
        self.assertEqual(picking.state, "done")

    def test_partial_complete_sets(self):
        picking = self._confirm_sale()
        self._set_quantities(picking, 1, 2)
        self.assertFalse(picking.check_complete_set())

    def test_quantity_mismatch(self):
        picking = self._confirm_sale()
        self._set_quantities(picking, 2, 3)
        self.assertTrue(picking.check_complete_set())
        with self.assertRaises(UserError):
            picking.button_validate()

    def test_missing_component(self):
        picking = self._confirm_sale()
        self._set_quantities(picking, 2, 4)
        picking.move_ids.filtered(lambda move: move.product_id == self.comp_1).unlink()
        self.assertIn("missing product", picking.check_complete_set())
        with self.assertRaises(UserError):
            picking.button_validate()

    def test_unrestricted_bom(self):
        self.bom.restrict_incomplete_delivery = False
        picking = self._confirm_sale()
        self._set_quantities(picking, 2, 3)
        self.assertFalse(picking.check_complete_set())
