from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPosStockOperation(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["pos.config"].create(
            {"name": "Stock Ops POS", "stock_ops_receipt": True, "stock_ops_delivery": True}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Ops Product", "is_storable": True, "available_in_pos": True}
        )
        cls.stock = cls.config.picking_type_id.warehouse_id.lot_stock_id
        cls.supplier = cls.env["res.partner"].create({"name": "Ops Supplier"})
        cls.Operation = cls.env["pos.stock.operation"]
        cls.env.user.group_ids += cls.env.ref("deltatech_pos_stock_ops.group_pos_stock_ops")

    def _qty(self):
        return self.env["stock.quant"]._get_available_quantity(self.product, self.stock)

    def _purchase(self, qty=10, picking_type=None):
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.supplier.id,
                "picking_type_id": (picking_type or self.config.stock_ops_receipt_type_id).id,
                "order_line": [
                    (0, 0, {"product_id": self.product.id, "product_qty": qty, "price_unit": 5.0}),
                ],
            }
        )
        order.button_confirm()
        return order

    # --- receipts -----------------------------------------------------
    def test_receipt_against_purchase_order(self):
        order = self._purchase(10)
        found = self.Operation.pos_search_receipts(self.config.id, order.name)
        self.assertEqual(len(found), 1)
        picking_data = found[0]
        self.assertEqual(picking_data["purchase_id"], order.id)
        move_id = picking_data["moves"][0]["id"]
        result = self.Operation.pos_receive_picking(
            self.config.id, picking_data["id"], [{"move_id": move_id, "qty": 10}]
        )
        self.assertEqual(result["state"], "done")
        self.assertEqual(self._qty(), 10)
        self.assertEqual(order.order_line.qty_received, 10)
        self.assertEqual(self.Operation.search([("picking_id", "=", result["picking_id"])]).purchase_id, order)

    def test_partial_receipt_leaves_a_backorder(self):
        order = self._purchase(10)
        picking = order.picking_ids
        result = self.Operation.pos_receive_picking(
            self.config.id, picking.id, [{"move_id": picking.move_ids.id, "qty": 4}]
        )
        self.assertEqual(result["state"], "done")
        self.assertEqual(self._qty(), 4)
        backorder = order.picking_ids - picking
        self.assertEqual(len(backorder), 1)
        self.assertEqual(backorder.move_ids.product_uom_qty, 6)

    def test_receipt_without_purchase_order_is_blocked(self):
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(
                self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": 5}]
            )

    def test_receipt_of_a_non_purchase_picking_is_blocked(self):
        picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.config.stock_ops_receipt_type_id.id,
                "location_id": self.env.ref("stock.stock_location_suppliers").id,
                "location_dest_id": self.stock.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 3,
                            "product_uom": self.product.uom_id.id,
                            "location_id": self.env.ref("stock.stock_location_suppliers").id,
                            "location_dest_id": self.stock.id,
                        },
                    )
                ],
            }
        )
        picking.action_confirm()
        with self.assertRaises(UserError):
            self.Operation.pos_receive_picking(self.config.id, picking.id, [{"move_id": picking.move_ids.id, "qty": 3}])

    def test_receipt_of_another_warehouse_order_is_blocked(self):
        other = self.env["stock.warehouse"].create({"name": "Other Ops WH", "code": "OOW"})
        order = self._purchase(5, picking_type=other.in_type_id)
        self.assertFalse(self.Operation.pos_search_receipts(self.config.id, order.name))
        picking = order.picking_ids
        with self.assertRaises(UserError):
            self.Operation.pos_receive_picking(self.config.id, picking.id, [{"move_id": picking.move_ids.id, "qty": 5}])

    def test_receipt_needs_a_received_quantity(self):
        picking = self._purchase(5).picking_ids
        with self.assertRaises(UserError):
            self.Operation.pos_receive_picking(self.config.id, picking.id, [{"move_id": picking.move_ids.id, "qty": 0}])

    # --- deliveries ---------------------------------------------------
    def _receive(self, qty):
        picking = self._purchase(qty).picking_ids
        self.Operation.pos_receive_picking(self.config.id, picking.id, [{"move_id": picking.move_ids.id, "qty": qty}])

    def test_delivery_decreases_stock(self):
        self._receive(10)
        self.Operation.pos_create_operation(
            self.config.id, "delivery", False, [{"product_id": self.product.id, "qty": 4}]
        )
        self.assertEqual(self._qty(), 6)

    def test_pack_unit_is_converted(self):
        self._receive(30)
        box = self.env["uom.uom"].create(
            {"name": "Test Box", "relative_factor": 12, "relative_uom_id": self.product.uom_id.id}
        )
        self.env["product.uom"].create({"uom_id": box.id, "product_id": self.product.id, "barcode": "BOX-OPS-1"})
        self.Operation.pos_create_operation(
            self.config.id, "delivery", False, [{"product_id": self.product.id, "qty": 2, "uom_id": box.id}]
        )
        self.assertEqual(self._qty(), 6)

    # --- guards -------------------------------------------------------
    def test_disabled_operation_is_refused(self):
        self.config.stock_ops_delivery = False
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(
                self.config.id, "delivery", False, [{"product_id": self.product.id, "qty": 1}]
            )

    def test_user_without_group_is_refused(self):
        user = self.env["res.users"].create(
            {
                "name": "Plain POS",
                "login": "plain_pos_ops",
                "group_ids": [(6, 0, [self.env.ref("point_of_sale.group_pos_user").id])],
            }
        )
        with self.assertRaises(AccessError):
            self.Operation.with_user(user).pos_create_operation(
                self.config.id, "delivery", False, [{"product_id": self.product.id, "qty": 1}]
            )

    def test_empty_or_negative_lines_are_refused(self):
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(self.config.id, "delivery", False, [])
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(
                self.config.id, "delivery", False, [{"product_id": self.product.id, "qty": -1}]
            )
