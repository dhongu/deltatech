from odoo.tests.common import TransactionCase


class TestPurchaseOrder(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "list_price": 100.0,
                "standard_price": 50.0,
            }
        )

        # Create a partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create a purchase order
        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 10,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )

    def test_compute_picking_status(self):
        # Confirm the purchase order
        self.purchase_order.button_confirm()

        # Check the picking status
        self.assertEqual(
            self.purchase_order.picking_status,
            "in_progress",
            "The picking status should be 'in_progress' after confirming the purchase order",
        )
        self.purchase_order.picking_ids[0].move_ids.write({"quantity": 10})
        # Validate the picking
        self.purchase_order.picking_ids[0].button_validate()
        self.purchase_order._compute_picking_status()
        # Check the picking status
        self.assertEqual(
            self.purchase_order.picking_status,
            "done",
            "The picking status should be 'done' after validating the picking",
        )

    def test_search_picking_status(self):
        # Search for purchase orders with picking status 'in_progress'
        in_progress_orders = self.env["purchase.order"].search([("picking_status", "=", "in_progress")])

        # Check if the created purchase order is in the result
        self.assertIn(
            self.purchase_order,
            in_progress_orders,
            "The created purchase order should be in the result when searching for 'in_progress' orders",
        )

        # Search for purchase orders with picking status 'done'
        done_orders = self.env["purchase.order"].search([("picking_status", "=", "done")])

        # Check if the created purchase order is not in the result
        self.assertNotIn(
            self.purchase_order,
            done_orders,
            "The created purchase order should not be in the result when searching for 'done' orders",
        )
