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
        cls.Operation = cls.env["pos.stock.operation"]
        cls.env.user.group_ids += cls.env.ref("deltatech_pos_stock_ops.group_pos_stock_ops")

    def _qty(self):
        return self.env["stock.quant"]._get_available_quantity(self.product, self.stock)

    def test_receipt_increases_stock(self):
        result = self.Operation.pos_create_operation(
            self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": 10}]
        )
        self.assertEqual(result["state"], "done")
        self.assertEqual(self._qty(), 10)
        self.assertEqual(self.env["stock.picking"].browse(result["picking_id"]).state, "done")

    def test_delivery_decreases_stock(self):
        self.Operation.pos_create_operation(
            self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": 10}]
        )
        self.Operation.pos_create_operation(
            self.config.id, "delivery", False, [{"product_id": self.product.id, "qty": 4}]
        )
        self.assertEqual(self._qty(), 6)

    def test_pack_unit_is_converted(self):
        box = self.env["uom.uom"].create(
            {"name": "Test Box", "relative_factor": 12, "relative_uom_id": self.product.uom_id.id}
        )
        self.env["product.uom"].create({"uom_id": box.id, "product_id": self.product.id, "barcode": "BOX-OPS-1"})
        self.Operation.pos_create_operation(
            self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": 2, "uom_id": box.id}]
        )
        self.assertEqual(self._qty(), 24)

    def test_disabled_operation_is_refused(self):
        self.config.stock_ops_receipt = False
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(
                self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": 1}]
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
                self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": 1}]
            )

    def test_empty_or_negative_lines_are_refused(self):
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(self.config.id, "receipt", False, [])
        with self.assertRaises(UserError):
            self.Operation.pos_create_operation(
                self.config.id, "receipt", False, [{"product_id": self.product.id, "qty": -1}]
            )
