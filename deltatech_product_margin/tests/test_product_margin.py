# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase


class TestProductMargin(TransactionCase):
    def setUp(self):
        super().setUp()
        self.ProductTemplate = self.env["product.template"]
        self.tax = self.env["account.tax"].create(
            {
                "name": "Test Tax",
                "amount": 10.0,
                "price_include": True,
            }
        )
        # Create a sample product
        self.product = self.ProductTemplate.create(
            {
                "name": "Test Product",
                "standard_price": 100.0,
                "list_price": 150.0,
            }
        )

        # Create a sample tax

        self.product.taxes_id = self.tax

    def test_compute_margin(self):
        # Ensure margin is correctly computed
        self.product._compute_margin()

    def test_set_inverse_margin(self):
        # Change the margin and set the inverse margin
        self.product.margin = 20.0
        self.product.set_inverse_margin()

        # Ensure list price is correctly computed
        list_price = self.product.standard_price / (1 - self.product.margin / 100)
        if self.product.taxes_id.price_include:
            list_price_tax = self.tax.with_context(force_price_include=False)._compute_amount(list_price, 1)
            list_price += list_price_tax

        self.assertAlmostEqual(self.product.list_price, list_price, places=2, msg="List price computation is incorrect")

        # Check if product.product method works correctly
        product_variant = self.product.product_variant_id
        product_variant.set_inverse_margin()
        self.assertAlmostEqual(
            product_variant.product_tmpl_id.list_price,
            list_price,
            places=2,
            msg="List price computation for product.product is incorrect",
        )
