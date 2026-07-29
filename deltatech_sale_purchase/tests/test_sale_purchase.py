# ©  2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestSalePurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.mto_route = cls.env.ref("stock.route_warehouse0_mto")
        cls.mto_route.active = True
        cls.buy_route = cls.env.ref("purchase_stock.route_warehouse0_buy")

        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.customer = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create(
            {
                "name": "Bought on Order",
                "is_storable": True,
                "route_ids": [(6, 0, (cls.buy_route | cls.mto_route).ids)],
                "seller_ids": [(0, 0, {"partner_id": cls.vendor.id, "price": 10.0})],
            }
        )

    def _new_sale_order(self, qty):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": qty})],
            }
        )
        order.action_confirm()
        return order

    def _purchase_lines(self, order):
        return order.order_line.move_ids.created_purchase_line_ids

    def test_cancel_removes_draft_purchase_lines(self):
        order = self._new_sale_order(3.0)
        purchase_lines = self._purchase_lines(order)
        self.assertEqual(len(purchase_lines), 1, "Confirming the order must generate a purchase line")
        self.assertEqual(purchase_lines.order_id.state, "draft")

        order._action_cancel()

        self.assertEqual(order.state, "cancel")
        self.assertFalse(purchase_lines.exists(), "The draft purchase line must be removed")

    def test_cancel_keeps_confirmed_purchase_lines(self):
        order = self._new_sale_order(3.0)
        purchase_lines = self._purchase_lines(order)
        purchase_lines.order_id.button_confirm()
        self.assertEqual(purchase_lines.order_id.state, "purchase")

        order._action_cancel()

        self.assertTrue(purchase_lines.exists(), "A confirmed purchase line is left to the buyer")

    def test_decrease_resizes_draft_purchase_line(self):
        """Guard on core behaviour, not on this module.

        On 18.0 the module had to resize the draft purchase line itself through
        `_log_decrease_ordered_quantity`; on 19.0 core propagates the decrease on
        its own and never logs an exception for the buyer. Should that change
        again, this test fails and the override has to come back.
        """
        order = self._new_sale_order(10.0)
        purchase_lines = self._purchase_lines(order)
        self.assertEqual(purchase_lines.product_qty, 10.0)
        purchase_order = purchase_lines.order_id
        activities_before = len(purchase_order.activity_ids)

        order.order_line.product_uom_qty = 4.0

        self.assertEqual(purchase_lines.product_qty, 4.0, "The draft purchase line follows the sale order")
        self.assertEqual(
            len(purchase_order.activity_ids),
            activities_before,
            "No exception activity is logged for the buyer",
        )
