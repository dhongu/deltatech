from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPickingStatusIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Storable", "is_storable": True, "standard_price": 50.0}
        )
        cls.service = cls.env["product.product"].create(
            {"name": "Test Service", "type": "service", "standard_price": 50.0}
        )

    def _create_order(self, product):
        return self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": product.id, "product_qty": 10, "price_unit": 100})],
            }
        )

    def test_search_includes_cancelled_order_in_progress(self):
        """#3434: a cancelled RFQ without receipts is displayed as in progress
        and must be found by searching that value."""
        order = self._create_order(self.service)
        order.button_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertEqual(order.picking_status, "in_progress")
        PO = self.env["purchase.order"]
        self.assertIn(order, PO.search([("picking_status", "=", "in_progress")]))
        self.assertNotIn(order, PO.search([("picking_status", "=", "done")]))
        self.assertIn(order, PO.search([("picking_status", "!=", "done")]))

    def test_search_includes_cancelled_order_done(self):
        """#3434: a cancelled order whose receipts are all cancelled is displayed
        as done and must be found by searching that value."""
        order = self._create_order(self.product)
        order.button_confirm()
        self.assertTrue(order.picking_ids)
        order.button_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertTrue(all(p.state == "cancel" for p in order.picking_ids))
        self.assertEqual(order.picking_status, "done")
        PO = self.env["purchase.order"]
        self.assertIn(order, PO.search([("picking_status", "=", "done")]))
        self.assertIn(order, PO.search([("picking_status", "not in", ["in_progress"])]))

    def test_status_refreshed_after_confirm(self):
        """#3435: the status read before confirmation must be recomputed after
        the order state changes in the same environment."""
        order = self._create_order(self.service)
        self.assertEqual(order.picking_status, "in_progress")
        order.button_confirm()
        self.assertEqual(order.state, "purchase")
        self.assertFalse(order.picking_ids)
        self.assertEqual(order.picking_status, "done")

    def test_status_refreshed_after_receipt_validated(self):
        """#3435: validating the receipt must refresh the status without an
        explicit recompute."""
        order = self._create_order(self.product)
        order.button_confirm()
        self.assertEqual(order.picking_status, "in_progress")
        picking = order.picking_ids
        picking.move_ids.write({"quantity": 10})
        picking.button_validate()
        self.assertEqual(picking.state, "done")
        self.assertEqual(order.picking_status, "done")

    def test_search_matches_compute(self):
        """#3434: for every operator, the search returns exactly the orders
        whose displayed status matches."""
        draft = self._create_order(self.product)
        service = self._create_order(self.service)
        service.button_confirm()
        confirmed = self._create_order(self.product)
        confirmed.button_confirm()
        cancelled = self._create_order(self.product)
        cancelled.button_confirm()
        cancelled.button_cancel()
        orders = draft | service | confirmed | cancelled
        PO = self.env["purchase.order"]
        for status in ("done", "in_progress"):
            expected = orders.filtered(lambda o, s=status: o.picking_status == s)
            self.assertEqual(PO.search([("id", "in", orders.ids), ("picking_status", "=", status)]), expected)
            self.assertEqual(PO.search([("id", "in", orders.ids), ("picking_status", "!=", status)]), orders - expected)
