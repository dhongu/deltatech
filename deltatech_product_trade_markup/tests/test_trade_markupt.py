from odoo.tests import common


class TestProductTradeMarkup(common.TransactionCase):
    def setUp(self):
        super().setUp()

        # Create a product template
        self.product_template = self.env["product.template"].create(
            {
                "name": "Test Product",
                "trade_markup": 20.0,
            }
        )

    def test_product_trade_markup(self):
        # Check if the trade markup was set correctly
        self.assertEqual(self.product_template.trade_markup, 20.0, "Trade markup was not set correctly")

    def test_product_product_trade_markup(self):
        # Create a product product
        self.product_product = self.env["product.product"].create(
            {
                "product_tmpl_id": self.product_template.id,
            }
        )
        self.product_template.set_inverse_trade_markup()
        self.product_product.set_inverse_trade_markup()
        # Check if the trade markup was set correctly
        self.assertEqual(self.product_product.trade_markup, 20.0, "Trade markup was not set correctly")
