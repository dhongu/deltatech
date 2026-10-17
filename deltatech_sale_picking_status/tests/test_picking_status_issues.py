from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPickingStatusIssues(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product = cls.env["product.product"].create(
            {"name": "Test Storable", "is_storable": True, "list_price": 150.0}
        )
        stock_location = cls.env.ref("stock.stock_location_stock")
        cls.env["stock.quant"]._update_available_quantity(cls.product, stock_location, 100)

    def _create_order(self):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 2, "price_unit": 150})],
            }
        )

    def _deliver(self, order):
        for picking in order.picking_ids:
            picking.move_ids.write({"quantity": 2})
            picking.button_validate()

    def test_status_after_reset_to_quotation(self):
        """#3470: a cancelled order reset to quotation must be in progress again."""
        order = self._create_order()
        order.action_confirm()
        self._deliver(order)
        self.assertEqual(order.picking_status, "done")
        order._action_cancel()
        self.assertEqual(order.state, "cancel")
        self.assertEqual(order.picking_status, "done")
        order.action_draft()
        self.assertEqual(order.state, "draft")
        self.assertEqual(order.picking_status, "in_progress")
        SO = self.env["sale.order"]
        self.assertIn(order, SO.search([("picking_status", "=", "in_progress")]))

    def test_status_after_cancel_without_pickings(self):
        """#3470: cancelling a quotation without pickings sets the status to done."""
        order = self._create_order()
        self.assertEqual(order.picking_status, "in_progress")
        order._action_cancel()
        self.assertEqual(order.picking_status, "done")
        self.assertIn(order, self.env["sale.order"].search([("picking_status", "=", "done")]))
