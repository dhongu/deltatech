# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import Form, tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPrepareBatch(TransactionCase):
    """BATCHTRANSFER-001: quantity preparation must use the Odoo 19 move line API."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.picking_type_out = cls.warehouse.out_type_id
        cls.uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_dozen = cls.env.ref("uom.product_uom_dozen")
        cls.partner = cls.env["res.partner"].create({"name": "Batch partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Batch product", "type": "consu", "is_storable": True, "default_code": "BP"}
        )
        cls.other_product = cls.env["product.product"].create(
            {"name": "Other batch product", "type": "consu", "is_storable": True}
        )
        cls.env["stock.quant"]._update_available_quantity(cls.product, cls.stock_location, 100)
        cls.env["stock.quant"]._update_available_quantity(cls.other_product, cls.stock_location, 100)

    def _create_picking(self, lines):
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.picking_type_out.id,
                "location_id": self.stock_location.id,
                "location_dest_id": self.customer_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                            "product_uom": (uom or product.uom_id).id,
                            "location_id": self.stock_location.id,
                            "location_dest_id": self.customer_location.id,
                        },
                    )
                    for product, qty, uom in lines
                ],
            }
        )
        picking.action_confirm()
        picking.action_assign()
        return picking

    def _create_batch(self, pickings):
        batch = self.env["stock.picking.batch"].create({"picking_ids": [(6, 0, pickings.ids)]})
        batch.action_confirm()
        return batch

    def _wizard(self, set_done_qty, lines):
        return self.env["stock.prepare.batch"].create(
            {
                "partner_id": self.partner.id,
                "set_done_qty": set_done_qty,
                "line_ids": [(0, 0, {"product_id": product.id, "quantity": qty}) for product, qty in lines],
            }
        )

    def _move_lines(self, picking, product=None):
        move_lines = picking.move_line_ids
        if product:
            move_lines = move_lines.filtered(lambda ml: ml.product_id == product)
        return move_lines

    def test_set_quantity_distributes_over_move_lines(self):
        picking_1 = self._create_picking([(self.product, 10, None)])
        picking_2 = self._create_picking([(self.product, 10, None)])
        batch = self._create_batch(picking_1 | picking_2)
        wizard = self._wizard(True, [(self.product, 12)])
        wizard.prepare_lines(batch)
        move_lines = self._move_lines(picking_1) | self._move_lines(picking_2)
        self.assertEqual(sorted(move_lines.mapped("quantity")), [2.0, 10.0])
        self.assertTrue(all(move_lines.mapped("picked")))
        self.assertEqual(wizard.line_ids.additional_quantity, 0.0)

    def test_set_quantity_additional_quantity(self):
        picking = self._create_picking([(self.product, 10, None)])
        batch = self._create_batch(picking)
        wizard = self._wizard(True, [(self.product, 15)])
        wizard.prepare_lines(batch)
        self.assertEqual(self._move_lines(picking).quantity, 10.0)
        self.assertTrue(self._move_lines(picking).picked)
        self.assertEqual(wizard.line_ids.additional_quantity, 5.0)

    def test_set_quantity_without_lines_picks_reserved(self):
        picking = self._create_picking([(self.product, 7, None)])
        batch = self._create_batch(picking)
        self._wizard(True, []).prepare_lines(batch)
        self.assertRecordValues(self._move_lines(picking), [{"quantity": 7.0, "picked": True}])

    def test_wo_quantity_reserves_requested_quantity(self):
        picking = self._create_picking([(self.product, 10, None), (self.other_product, 5, None)])
        batch = self._create_batch(picking)
        wizard = self._wizard(False, [(self.product, 4)])
        wizard.prepare_lines(batch)
        self.assertRecordValues(self._move_lines(picking, self.product), [{"quantity": 4.0, "picked": False}])
        # products not requested in the wizard are no longer reserved
        self.assertEqual(sum(self._move_lines(picking, self.other_product).mapped("quantity")), 0.0)
        self.assertEqual(wizard.line_ids.additional_quantity, 0.0)

    def test_different_units(self):
        picking = self._create_picking([(self.product, 2, self.uom_dozen)])
        batch = self._create_batch(picking)
        move_line = self._move_lines(picking)
        self.assertEqual(move_line.product_uom_id, self.uom_dozen)
        self.assertEqual(move_line.quantity, 2.0)
        wizard = self._wizard(True, [(self.product, 30)])
        wizard.prepare_lines(batch)
        # 2 dozens = 24 units are allocated, 6 units remain additional
        self.assertRecordValues(move_line, [{"quantity": 2.0, "picked": True}])
        self.assertEqual(wizard.line_ids.additional_quantity, 6.0)

        picking_2 = self._create_picking([(self.product, 2, self.uom_dozen)])
        batch_2 = self._create_batch(picking_2)
        self._wizard(True, [(self.product, 6)]).prepare_lines(batch_2)
        self.assertRecordValues(self._move_lines(picking_2), [{"quantity": 0.5, "picked": True}])

    def test_product_not_found(self):
        picking = self._create_picking([(self.product, 10, None)])
        batch = self._create_batch(picking)
        with self.assertRaises(UserError):
            self._wizard(True, [(self.other_product, 1)]).prepare_lines(batch)

    def test_attach_purchase_pickings(self):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_qty": 10, "price_unit": 1})],
            }
        )
        order.button_confirm()
        wizard_form = Form(self.env["stock.prepare.batch"])
        wizard_form.partner_id = self.partner
        wizard_form.mode = "purchase"
        wizard_form.set_done_qty = True
        with wizard_form.line_ids.new() as line:
            line.product_id = self.product
            line.quantity = 4
        wizard = wizard_form.save()
        action = wizard.attach_pickings()
        batch = self.env["stock.picking.batch"].search(action["domain"])
        self.assertEqual(batch.picking_ids, order.picking_ids)
        self.assertRecordValues(batch.move_line_ids, [{"quantity": 4.0, "picked": True}])
