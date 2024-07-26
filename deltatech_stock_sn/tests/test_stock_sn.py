from odoo.tests.common import TransactionCase


class TestStockCustomizations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.StockLocation = self.env["stock.location"]
        self.StockProductionLot = self.env["stock.lot"]
        self.StockMoveLine = self.env["stock.move.line"]
        self.StockQuant = self.env["stock.quant"]
        self.Product = self.env["product.product"]

        # Create a product for testing
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "type": "product",
                # 'sale_line_warn': 'no-message',
                # Add default value for sale_line_warn
            }
        )

        # Create a stock location
        self.location = self.StockLocation.create(
            {
                "name": "Test Location",
                "usage": "internal",
            }
        )

        # Create a stock lot
        self.lot = self.StockProductionLot.create(
            {
                "name": "Test Lot",
                "product_id": self.product.id,
            }
        )

        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
            }
        )

    def test_onchange_hide_lot(self):
        # Test the onchange for hide_lot
        self.location.usage = "internal"
        self.location.hide_lot = True
        self.location.onchange_hide_lot()
        self.assertFalse(self.location.hide_lot, "Hide lot should be False for internal usage")

    def test_compute_stock_available(self):
        # Create stock quants for the lot in the internal location
        self.StockQuant.create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "lot_id": self.lot.id,
                "quantity": 10,
            }
        )

        # Check computed fields
        self.lot._compute_stock_available()
        self.assertEqual(self.lot.stock_available, 10.0, "Stock available should be 10.0")
        self.assertTrue(self.lot.active, "Lot should be active when stock is available")

    def test_stock_move_line_lot_name(self):
        # Test creation of stock move line with auto-generated lot name
        move_line = self.StockMoveLine.create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "location_dest_id": self.location.id,
                "lot_name": "/",
                "company_id": self.company.id,
            }
        )
        self.assertNotEqual(move_line.lot_name, "/", "Lot name should be auto-generated")

        # Test write method of stock move line with auto-generated lot name
        move_line.write({"lot_name": "/"})
        self.assertNotEqual(move_line.lot_name, "/", "Lot name should be auto-generated on write")

    def test_hide_lot_location(self):
        # Create a stock quant in a location with hide_lot set to True
        hide_location = self.StockLocation.create(
            {
                "name": "Hide Lot Location",
                "usage": "internal",
                "hide_lot": True,
            }
        )
        self.StockQuant.create(
            {
                "product_id": self.product.id,
                "location_id": hide_location.id,
                "lot_id": self.lot.id,
                "quantity": 5,
            }
        )

        # Check the lot's availability in hide_lot location
        self.lot._compute_stock_available()
        self.assertEqual(self.lot.stock_available, 5.0, "Stock available should not consider hidden lot locations")

    def test_multiple_lots(self):
        # Create another lot and stock quant for the product
        lot2 = self.StockProductionLot.create(
            {
                "name": "Test Lot 2",
                "product_id": self.product.id,
            }
        )
        self.StockQuant.create(
            {
                "product_id": self.product.id,
                "location_id": self.location.id,
                "lot_id": lot2.id,
                "quantity": 15,
            }
        )

        # Check the availability for multiple lots
        lot2._compute_stock_available()
        self.assertEqual(lot2.stock_available, 15.0, "Stock available should be 15.0 for the second lot")
        self.assertTrue(lot2.active, "Second lot should be active when stock is available")
