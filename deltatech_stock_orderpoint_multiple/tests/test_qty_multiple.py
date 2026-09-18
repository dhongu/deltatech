# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestStockOrderpointQtyMultiple(TransactionCase):
    def setUp(self):
        super().setUp()
        self.warehouse = self.env["stock.warehouse"].search([], limit=1)
        self.product = self.env["product.product"].create(
            {
                "name": "Test product qty multiple",
                "is_storable": True,
            }
        )

    def _make_orderpoint(self, qty_multiple, product_max_qty, product_min_qty=500):
        return self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": self.product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "warehouse_id": self.warehouse.id,
                "product_min_qty": product_min_qty,
                "product_max_qty": product_max_qty,
                "qty_multiple": qty_multiple,
            }
        )

    def test_rounds_down_to_multiple_when_max_qty_set(self):
        orderpoint = self._make_orderpoint(qty_multiple=100, product_max_qty=1000)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(1138), 1100)

    def test_rounds_up_to_multiple_when_no_max_qty(self):
        # product_min_qty must be <= product_max_qty (Odoo constraint); the
        # "no cap" case is min = max = 0 (manual/uncapped orderpoint).
        orderpoint = self._make_orderpoint(qty_multiple=100, product_max_qty=0, product_min_qty=0)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(38), 100)

    def test_no_rounding_when_multiple_is_zero(self):
        orderpoint = self._make_orderpoint(qty_multiple=0, product_max_qty=1000)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(1138), 1138)

    def test_no_rounding_when_already_a_multiple(self):
        orderpoint = self._make_orderpoint(qty_multiple=100, product_max_qty=1000)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(1100), 1100)

    def test_never_rounds_down_to_zero_when_need_is_below_multiple(self):
        # Regression: rounding down a need smaller than the multiple yields 0, and
        # the rule then never orders anything - a cap below the multiple silently
        # disables replenishment. Order one full multiple instead of nothing.
        orderpoint = self._make_orderpoint(qty_multiple=10, product_max_qty=6, product_min_qty=5)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(6), 10)

    def test_rounds_down_when_result_stays_positive(self):
        # The Odoo <= 18.0 "stay within the cap" behaviour must be preserved
        # whenever rounding down still leaves something to order.
        orderpoint = self._make_orderpoint(qty_multiple=10, product_max_qty=22, product_min_qty=10)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(16), 10)

    def test_rounds_up_when_multiple_equals_need(self):
        # Exactly one multiple short: rounding down would also give 0.
        orderpoint = self._make_orderpoint(qty_multiple=10, product_max_qty=10, product_min_qty=5)
        self.assertEqual(orderpoint._get_multiple_rounded_qty(9), 10)

    def test_native_replenishment_uom_is_not_shadowed_by_default(self):
        # Regression: qty_multiple must default to "unset" (0) so it never
        # silently overrides the native `replenishment_uom_id` mechanism on
        # orderpoints that were never configured with a legacy multiple.
        dozen = self.env["uom.uom"].create(
            {
                "name": "Test Dozen (qty_multiple regression)",
                "relative_uom_id": self.product.uom_id.id,
                "relative_factor": 12,
            }
        )
        self.product.write({"uom_ids": [(4, dozen.id)]})
        orderpoint = self.env["stock.warehouse.orderpoint"].create(
            {
                "product_id": self.product.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "warehouse_id": self.warehouse.id,
                "product_min_qty": 0,
                "product_max_qty": 0,
                "replenishment_uom_id": dozen.id,
            }
        )
        self.assertEqual(orderpoint.qty_multiple, 0, "qty_multiple must default to 0 (unset)")
        self.assertEqual(
            orderpoint._get_multiple_rounded_qty(5),
            12,
            "Native replenishment_uom_id must be respected when qty_multiple is unset",
        )
