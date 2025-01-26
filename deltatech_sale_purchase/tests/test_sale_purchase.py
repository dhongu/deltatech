from odoo.tests.common import TransactionCase


class TestSaleOrderAndStockRule(TransactionCase):
    def setUp(self):
        super().setUp()

        # Setup test data
        self.SaleOrder = self.env["sale.order"]
        self.StockRule = self.env["stock.rule"]
        self.Product = self.env["product.product"]

        # Create a product
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "type": "product",
                "weight": 1.0,
            }
        )
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )
        # Create a sale order
        self.sale_order = self.SaleOrder.create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                        },
                    )
                ],
            }
        )

    def test_action_cancel(self):
        # Confirm the sale order
        self.sale_order.action_confirm()

        # Cancel the sale order
        self.sale_order._action_cancel()

        # Check that the sale order is cancelled
        self.assertEqual(self.sale_order.state, "cancel")

        # Check that the purchase order line is deleted
        for line in self.sale_order.order_line:
            for move in line.move_ids:
                self.assertFalse(move.created_purchase_line_ids)

    def test_make_po_get_domain(self):
        # Get the stock location of the current company
        stock_location = (
            self.env["stock.warehouse"].search([("company_id", "=", self.env.user.company_id.id)], limit=1).lot_stock_id
        )
        # Get the 'Buy' route
        buy_route = self.env.ref("purchase_stock.route_warehouse0_buy")

        # Create a stock rule
        stock_rule = self.StockRule.create(
            {
                "name": "Test Rule",
                "action": "buy",
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "group_propagation_option": "none",
                "location_dest_id": stock_location.id,
                "route_id": buy_route.id,  # Add this line
            }
        )

        # The rest of your test case...

        # Call the _make_po_get_domain method
        # Call the _make_po_get_domain method
        stock_rule._make_po_get_domain(
            self.env.user.company_id,  # Pass the recordset, not the ID
            {"group_id": self.env["procurement.group"].create({"name": "Test Group"}).id},
            self.partner,
        )
