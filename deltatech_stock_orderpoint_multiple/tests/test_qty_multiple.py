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
