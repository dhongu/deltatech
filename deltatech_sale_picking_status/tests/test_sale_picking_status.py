from odoo.tests.common import TransactionCase


class TestStockPickingAndSaleOrder(TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a test partner
        self.partner_a = self.env["res.partner"].create({"name": "Test Partner"})

        # Create test products
        self.product_a = self.env["product.product"].create(
            {
                "name": "Test Product A",
                "type": "product",
                "standard_price": 100,
                "list_price": 150,
            }
        )
        self.product_b = self.env["product.product"].create(
            {
                "name": "Test Product B",
                "type": "product",
                "standard_price": 70,
                "list_price": 150,
            }
        )

        # Update stock quantities
        self.stock_location = self.env.ref("stock.stock_location_stock")
        self.env["stock.quant"]._update_available_quantity(self.product_a, self.stock_location, 1000)
        self.env["stock.quant"]._update_available_quantity(self.product_b, self.stock_location, 1000)

        # Create a sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner_a.id,
            }
        )

        # Create sale order lines
        self.sale_order_line_a = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product_a.id,
                "product_uom_qty": 1.0,
                "price_unit": 150.0,
            }
        )
        self.sale_order_line_b = self.env["sale.order.line"].create(
            {
                "order_id": self.sale_order.id,
                "product_id": self.product_b.id,
                "product_uom_qty": 2.0,
                "price_unit": 150.0,
            }
        )

    def test_picking_status(self):
        # Confirm the sale order
        self.sale_order.action_confirm()
        self.assertEqual(
            self.sale_order.picking_status,
            "in_progress",
            "Picking status should be 'in_progress' after confirming the sale order",
        )

        # Validate the stock move associated with the sale order
        for picking in self.sale_order.picking_ids:
            picking.action_confirm()
            picking.action_assign()
            for move_line in picking.move_line_ids:
                move_line.quantity = move_line.quantity_product_uom
            picking.button_validate()

        self.sale_order._compute_picking_status()
        self.assertEqual(
            self.sale_order.picking_status, "done", "Picking status should be 'done' after validating the pickings"
        )

        # Cancel the sale order and check the picking status
        self.sale_order.action_cancel()
        self.assertEqual(
            self.sale_order.picking_status, "done", "Picking status should be 'done' after cancelling the sale order"
        )
