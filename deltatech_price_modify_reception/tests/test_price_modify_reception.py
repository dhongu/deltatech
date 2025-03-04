from odoo.tests.common import TransactionCase


class TestCanModifyPriceList(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Company = self.env["res.company"]
        self.ResConfigSettings = self.env["res.config.settings"]
        self.Picking = self.env["stock.picking"]
        self.StockMove = self.env["stock.move"]
        self.Product = self.env["product.product"]
        self.user = self.env.user

        # Create a test company and set can_modify_price_list_at_reception to True
        self.company = self.Company.create(
            {
                "name": "Test Company",
                "can_modify_price_list_at_reception": True,
            }
        )

        # Set the user's company to the test company
        self.user.company_id = self.company

        # Create a product
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "list_price": 100.0,
            }
        )

        # Create a picking
        self.picking = self.Picking.create(
            {
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
            }
        )
        self.location_source = self.env["stock.location"].create(
            {
                "name": "Source Location",
                "usage": "internal",
            }
        )
        self.location_dest = self.env["stock.location"].create(
            {
                "name": "Destination Location",
                "usage": "internal",
            }
        )
        # Create a stock move
        self.stock_move = self.StockMove.create(
            {
                "name": "Test Move",
                "product_id": self.product.id,
                "product_uom_qty": 10,
                "location_id": self.location_source.id,
                "location_dest_id": self.location_dest.id,
                "picking_id": self.picking.id,
            }
        )

    def test_can_modify_price_list_setting(self):
        # Check the company setting
        self.assertTrue(self.company.can_modify_price_list_at_reception, "The company setting should be True.")

        # Check the setting in res.config.settings
        config = self.ResConfigSettings.create({})
        self.assertEqual(
            config.can_modify_price_list_at_reception,
            self.company.can_modify_price_list_at_reception,
            "The res.config.settings should reflect the company setting.",
        )

    def test_stock_move_price_list_field(self):
        # Check if the price_list field is modifiable based on the can_modify_price_list_at_reception setting
        self.assertEqual(
            self.stock_move.price_list,
            self.product.list_price,
            "The stock move's price_list should reflect the product's list price.",
        )

        if self.company.can_modify_price_list_at_reception:
            self.stock_move.price_list = 120.0
            self.assertEqual(self.stock_move.price_list, 120.0, "The price_list should be modifiable.")
