from odoo.tests.common import TransactionCase


class TestStockOperations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
                "tracking": "lot",  # Product tracking by lot
            }
        )
        self.location = self.env["stock.location"].create(
            {
                "name": "Test Location",
                "usage": "internal",
            }
        )

        # Create a company to use in the tests
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "currency_id": self.ref("base.USD"),  # Replace with appropriate currency ID
            }
        )
        # self.stock_picking_type= self.env['stock.picking.type'].create({
        #     'name': 'Test Picking Type',
        #     'code': 'incoming',
        #     'sequence_id': 'TR'
        # })

    def test_stock_picking_button_validate(self):
        StockPicking = self.env["stock.picking"]

        # Create a stock picking for incoming products with tracking by lot
        picking = StockPicking.create(
            {
                "picking_type_id": self.ref("stock.picking_type_in"),
                "location_id": self.location.id,
                "location_dest_id": self.location.id,
            }
        )

        # Create a stock move line with product tracking by lot
        move_line = self.env["stock.move.line"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "location_dest_id": self.location.id,
                "picking_id": picking.id,
                "qty_done": 1.0,
            }
        )

        # Validate picking
        picking.button_validate()

        # Check if lot name is generated for move line
        self.assertTrue(move_line.lot_name, "Expected lot name to be generated for move line")

    def test_production_lot_compute_location(self):
        ProductionLot = self.env["stock.lot"]

        # Create a production lot with associated quants
        lot = ProductionLot.create(
            {
                "name": "TESTLOT001",
                "product_id": self.product.id,
            }
        )
        self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "quantity": 10.0,
                "lot_id": lot.id,
            }
        )

        # Compute location for the production lot
        lot._compute_location()

        # Check computed location
        self.assertEqual(lot.location_id, self.location, "Expected location to be computed correctly")

    def test_stock_picking_button_validate_no_lot_error(self):
        StockPicking = self.env["stock.picking"]

        # Create a stock picking for incoming products with tracking by lot, but no lot name provided
        picking = StockPicking.create(
            {
                "picking_type_id": self.ref("stock.picking_type_in"),
                "location_id": self.location.id,
                "location_dest_id": self.location.id,
            }
        )

        # Create a stock move line with product tracking by lot, but without lot name
        self.env["stock.move.line"].create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "location_dest_id": self.location.id,
                "picking_id": picking.id,
                "qty_done": 1.0,
            }
        )
