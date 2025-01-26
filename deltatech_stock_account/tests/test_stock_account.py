# from odoo.tests.common import TransactionCase
#
#
# class TestStockPickingAmount(TransactionCase):
#     def setUp(self):
#         super().setUp()
#
#         # Get or create a test currency
#         self.currency = self.env["res.currency"].search([("name", "=", "USD")], limit=1)
#         if not self.currency:
#             self.currency = self.env["res.currency"].create(
#                 {
#                     "name": "USD",
#                     "symbol": "$",
#                     "rounding": 0.01,
#                 }
#             )
#
#         # Create a test partner
#         self.partner = self.env["res.partner"].create({"name": "Test Partner"})
#
#         # Create test products
#         self.product_a = self.env["product.product"].create(
#             {
#                 "name": "Product A",
#                 "type": "product",
#                 "standard_price": 100,
#                 "list_price": 150,
#             }
#         )
#
#         self.product_b = self.env["product.product"].create(
#             {
#                 "name": "Product B",
#                 "type": "product",
#                 "standard_price": 70,
#                 "list_price": 120,
#             }
#         )
#
#         # Create a test warehouse and picking type
#         self.warehouse = self.env["stock.warehouse"].create({"name": "Warehouse 1", "code": "WH1"})
#         self.picking_type = self.env["stock.picking.type"].create(
#             {"name": "Delivery Orders", "code": "outgoing", "sequence_code": "OUT", "warehouse_id": self.warehouse.id}
#         )
#
#         # Create a stock picking
#         self.picking = self.env["stock.picking"].create(
#             {
#                 "partner_id": self.partner.id,
#                 "picking_type_id": self.picking_type.id,
#                 "location_id": self.warehouse.lot_stock_id.id,
#                 "location_dest_id": self.env.ref("stock.stock_location_customers").id,
#                 "currency_id": self.currency.id,
#             }
#         )
#         self.env["stock.quant"].create(
#             {
#                 "product_id": self.product_a.id,
#                 "location_id": self.warehouse.lot_stock_id.id,
#                 "quantity": 100,
#             }
#         )
#
#         # Set initial stock for product_b
#         self.env["stock.quant"].create(
#             {
#                 "product_id": self.product_b.id,
#                 "location_id": self.warehouse.lot_stock_id.id,
#                 "quantity": 100,
#             }
#         )
#         # Create stock moves
#         self.move_a = self.env["stock.move"].create(
#             {
#                 "name": "Move A",
#                 "product_id": self.product_a.id,
#                 "product_uom_qty": 10,
#                 "product_uom": self.product_a.uom_id.id,
#                 "picking_id": self.picking.id,
#                 "location_id": self.warehouse.lot_stock_id.id,
#                 "location_dest_id": self.env.ref("stock.stock_location_customers").id,
#             }
#         )
#
#         self.move_b = self.env["stock.move"].create(
#             {
#                 "name": "Move B",
#                 "product_id": self.product_b.id,
#                 "product_uom_qty": 5,
#                 "product_uom": self.product_b.uom_id.id,
#                 "picking_id": self.picking.id,
#                 "location_id": self.warehouse.lot_stock_id.id,
#                 "location_dest_id": self.env.ref("stock.stock_location_customers").id,
#             }
#         )
#
#         # Confirm the picking and move to 'done' state to create valuation layers
#         self.picking.action_confirm()
#         self.picking.action_assign()
#         for move in self.picking.move_ids:
#             move.quantity = move.product_uom_qty
#         self.picking.button_validate()
#
#     def test_compute_amount(self):
#         # Check if the amount is computed correctly
#         self.picking._compute_amount()
#         expected_amount = sum(move.product_uom_qty * move.product_id.standard_price for move in self.picking.move_ids)
#         self.assertEqual(self.picking.amount, (-1) * expected_amount, "The computed amount is incorrect.")
