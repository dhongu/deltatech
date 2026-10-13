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

    def _new_sale_order(self, qty, uom=None):
        line_vals = {"product_id": self.product.id, "product_uom_qty": qty}
        if uom:
            line_vals["product_uom_id"] = uom.id
        order = self.env["sale.order"].create(
            {
                "partner_id": self.customer.id,
                "order_line": [(0, 0, line_vals)],
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

    def _new_shared_sale_orders(self, qty_a, qty_b, uom_a=None):
        """Two sale orders whose MTO needs land on the same draft purchase line.

        With the default `On Order` grouping core keeps MTO needs of different
        sale orders on separate RFQs; only a Daily/Weekly/Always vendor merges them.
        """
        self.vendor.group_rfq = "all"
        order_a = self._new_sale_order(qty_a, uom_a)
        order_b = self._new_sale_order(qty_b)
        purchase_line = self._purchase_lines(order_a)
        self.assertEqual(len(purchase_line), 1)
        self.assertEqual(purchase_line, self._purchase_lines(order_b), "Both sales must share the purchase line")
        return order_a, order_b, purchase_line

    def test_cancel_keeps_purchase_line_shared_with_other_sale(self):
        order_a, order_b, purchase_line = self._new_shared_sale_orders(5.0, 7.0)
        self.assertEqual(purchase_line.product_qty, 12.0)
        move_b = order_b.order_line.move_ids

        order_a._action_cancel()

        self.assertTrue(purchase_line.exists(), "The line still supplies the other sale order")
        self.assertEqual(purchase_line.product_qty, 7.0, "Only the demand of the cancelled sale is removed")
        self.assertEqual(purchase_line.move_dest_ids, move_b)
        self.assertNotEqual(move_b.state, "cancel")
        self.assertEqual(move_b.procure_method, "make_to_order")

        order_b._action_cancel()

        self.assertFalse(purchase_line.exists(), "Once no active sale is left the draft line is removed")

    def test_cancel_shared_purchase_line_converts_uom(self):
        dozen = self.env.ref("uom.product_uom_dozen")
        order_a, order_b, purchase_line = self._new_shared_sale_orders(1.0, 7.0, uom_a=dozen)
        self.assertEqual(purchase_line.product_qty, 19.0)

        order_a._action_cancel()

        self.assertEqual(purchase_line.product_qty, 7.0)

    def test_cancel_keeps_shared_confirmed_purchase_line(self):
        order_a, order_b, purchase_line = self._new_shared_sale_orders(5.0, 7.0)
        purchase_line.order_id.button_confirm()

        order_a._action_cancel()

        self.assertTrue(purchase_line.exists())
        self.assertEqual(purchase_line.product_qty, 12.0, "A confirmed purchase line is left to the buyer")
