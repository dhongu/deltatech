# ©  2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPurchaseStock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.warehouse = cls.env["stock.warehouse"].search([("company_id", "=", cls.env.company.id)], limit=1)
        cls.buy_route = cls.env.ref("purchase_stock.route_warehouse0_buy")
        cls.vendor = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls._new_product("Replenished Product", 10.0)

    @classmethod
    def _new_product(cls, name, price):
        return cls.env["product.product"].create(
            {
                "name": name,
                "is_storable": True,
                "route_ids": [(6, 0, cls.buy_route.ids)],
                "seller_ids": [(0, 0, {"partner_id": cls.vendor.id, "price": price})],
            }
        )

    def _replenish(self, product, qty):
        """Trigger the buy rule through a manual reordering rule.

        A rule may already exist for the product: `deltatech_auto_reorder_rule`
        creates one on every new product, and only one rule is allowed per
        product, location and company.
        """
        values = {"product_min_qty": qty, "product_max_qty": qty, "trigger": "manual"}
        orderpoint = self.env["stock.warehouse.orderpoint"].search(
            [("product_id", "=", product.id), ("location_id", "=", self.warehouse.lot_stock_id.id)],
            limit=1,
        )
        if orderpoint:
            orderpoint.write(values)
        else:
            orderpoint = self.env["stock.warehouse.orderpoint"].create(
                {"product_id": product.id, "warehouse_id": self.warehouse.id, **values}
            )
        orderpoint.action_replenish()
        return orderpoint

    def _vendor_orders(self):
        return self.env["purchase.order"].search([("partner_id", "=", self.vendor.id)])

    def _new_manual_order(self):
        """Draft order matching the core domain of _make_po_get_domain."""
        return self.env["purchase.order"].create(
            {
                "partner_id": self.vendor.id,
                "user_id": self.vendor.buyer_id.id,
                "picking_type_id": self.warehouse.in_type_id.id,
                "company_id": self.env.company.id,
            }
        )

    def test_replenishment_order_is_flagged(self):
        self._replenish(self.product, 5.0)
        order = self._vendor_orders()
        self.assertEqual(len(order), 1)
        self.assertTrue(order.from_replenishment)

    def test_replenishments_are_merged_together(self):
        self._replenish(self.product, 5.0)
        other_product = self._new_product("Other Replenished Product", 20.0)
        self._replenish(other_product, 3.0)

        orders = self._vendor_orders()
        self.assertEqual(len(orders), 1, "Both replenishments belong to the same order")
        self.assertEqual(orders.order_line.product_id, self.product | other_product)

    def test_manual_order_is_not_used_by_replenishment(self):
        manual_order = self._new_manual_order()
        self.assertFalse(manual_order.from_replenishment)

        self._replenish(self.product, 5.0)

        self.assertFalse(manual_order.order_line, "Manual order must stay untouched")
        replenishment_orders = self._vendor_orders() - manual_order
        self.assertEqual(len(replenishment_orders), 1)
        self.assertTrue(replenishment_orders.from_replenishment)
        self.assertEqual(replenishment_orders.order_line.product_id, self.product)
