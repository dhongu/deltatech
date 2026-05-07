# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tests import tagged

from odoo.addons.website_sale.tests.common import WebsiteSaleCommon


@tagged("post_install", "-at_install")
class TestWebsiteSaleCostPrice(WebsiteSaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website.prevent_zero_price_sale = True

        # Create a product for testing
        cls.test_product = cls.env["product.product"].create(
            {
                "name": "Test Cost Price Product",
                "list_price": 100.0,
                "standard_price": 80.0,
                "website_published": True,
            }
        )

    def test_01_price_higher_than_cost(self):
        """Test that product is allowed when price is higher than cost"""
        self.test_product.list_price = 100.0
        self.test_product.standard_price = 80.0

        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        self.assertFalse(info["prevent_zero_price_sale"], "Sale should NOT be prevented when price > cost")
        self.assertTrue(self.test_product._website_show_quick_add(), "Quick add should be allowed")
        self.assertTrue(self.test_product._is_add_to_cart_allowed(), "Add to cart should be allowed")

    def test_02_price_lower_than_cost(self):
        """Test that product is NOT allowed when price is lower than cost"""
        self.test_product.list_price = 70.0
        self.test_product.standard_price = 80.0

        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        self.assertTrue(info["prevent_zero_price_sale"], "Sale SHOULD be prevented when price < cost")
        self.assertFalse(self.test_product._website_show_quick_add(), "Quick add should NOT be allowed")
        # _is_add_to_cart_allowed returns True for system user, so we check without system user or just check logic
        # For simplicity, we know we are running as admin in tests usually, so we might need to check with a different user

        public_user = self.env.ref("base.public_user")
        self.assertFalse(
            self.test_product.with_user(public_user)._is_add_to_cart_allowed(),
            "Add to cart should NOT be allowed for public user",
        )

    def test_03_price_with_margin(self):
        """Test that margin is correctly applied"""
        self.website.cost_price_margin_percentage = 10.0  # 10% margin

        # Cost 80 + 10% = 88.
        # Price 85 should be rejected.
        self.test_product.list_price = 85.0
        self.test_product.standard_price = 80.0

        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        self.assertTrue(info["prevent_zero_price_sale"], "Sale SHOULD be prevented when price < cost + margin")

        # Price 90 should be accepted.
        self.test_product.list_price = 90.0
        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        self.assertFalse(info["prevent_zero_price_sale"], "Sale should NOT be prevented when price > cost + margin")

    def test_04_tax_adjustment(self):
        """Test tax adjustment logic"""
        tax = self.env["account.tax"].create(
            {
                "name": "Test Tax 20%",
                "amount": 20.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
            }
        )
        self.test_product.taxes_id = [(6, 0, [tax.id])]

        # Case 1: Website shows tax included, Cost does not include tax.
        self.website.show_line_subtotals_tax_selection = "tax_included"
        self.website.cost_price_include_tax = False

        self.test_product.standard_price = 100.0  # Cost excluded tax = 100. Cost included tax = 120.
        self.test_product.list_price = 110.0  # This is what will be used as base for website price (tax included)
        # Actually in _get_combination_info, 'price' will be 110 * 1.2 = 132 (if pricelist has it as 110)
        # Let's verify our logic.

        # We need to make sure the pricelist doesn't have taxes included/excluded settings that conflict.
        # Standard Odoo: list_price is tax excluded.
        # _get_combination_info applies taxes to the price obtained from pricelist.

        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        # price should be 110 * 1.2 = 132.0
        # cost_price for comparison should be 100 * 1.2 = 120.0 (since website is tax_included and cost is tax_excluded)
        # 132 > 120 -> allowed.
        self.assertFalse(info["prevent_zero_price_sale"], "Should be allowed: 132 > 120")

        self.test_product.list_price = 90.0
        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        # price = 90 * 1.2 = 108.0
        # cost = 120.0
        # 108 < 120 -> prevented.
        self.assertTrue(info["prevent_zero_price_sale"], "Should be prevented: 108 < 120")

    def test_05_prevent_zero_price_sale_disabled(self):
        """Test that if the main setting is disabled, our check is also skipped"""
        self.website.prevent_zero_price_sale = False
        self.test_product.list_price = 10.0
        self.test_product.standard_price = 100.0

        info = self.test_product.product_tmpl_id._get_combination_info(product_id=self.test_product.id)
        self.assertFalse(info["prevent_zero_price_sale"], "Should NOT be prevented because main toggle is OFF")
