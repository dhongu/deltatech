from odoo.tests.common import TransactionCase


class TestProductReorderingLimit(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.warehouse = cls.env["stock.warehouse"].search([], limit=1)
        cls.stock_location = cls.warehouse.lot_stock_id

        cls.product_tmpl = cls.env["product.template"].create(
            {
                "name": "Test Product Template",
                "is_storable": True,
                "total_minimum": 10.0,
                "total_maximum": 20.0,
            }
        )
        cls.product = cls.product_tmpl.product_variant_id

    def test_reordering_limit_defaults(self):
        """Test default values for new products."""
        new_product_tmpl = self.env["product.template"].create({"name": "New Product"})
        self.assertEqual(new_product_tmpl.total_minimum, 0.0)
        self.assertEqual(new_product_tmpl.total_maximum, 0.0)
        self.assertFalse(new_product_tmpl.is_below_min)

    def test_reordering_limit_computation(self):
        """Test the computation of is_below_min field."""
        self.product_tmpl.total_minimum = 10.0

        # Initial state: 0 quantity, below 10.0
        self.assertTrue(self.product_tmpl.is_below_min)

        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 5)
        self.product_tmpl.invalidate_recordset(["qty_available", "is_below_min"])
        self.assertTrue(self.product_tmpl.is_below_min)

    def test_reordering_limit_search(self):
        """Test the search logic for is_below_min field."""
        self.product_tmpl.total_minimum = 10.0

        # Search for products below minimum
        below_min_products = self.env["product.template"].search([("is_below_min", "=", True)])
        self.assertIn(self.product_tmpl, below_min_products)

        # Add stock so it's not below minimum anymore
        self.env["stock.quant"]._update_available_quantity(self.product, self.stock_location, 15)

        # Flush the changes to the database as search uses SQL
        self.env.flush_all()

        below_min_products = self.env["product.template"].search([("is_below_min", "=", True)])
        self.assertNotIn(self.product_tmpl, below_min_products)

        # Search for products NOT below minimum
        not_below_min_products = self.env["product.template"].search([("is_below_min", "=", False)])
        self.assertIn(self.product_tmpl, not_below_min_products)
