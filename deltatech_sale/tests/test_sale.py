from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestSaleOrderLine(TransactionCase):

    def setUp(self):
        super().setUp()
        # Set up the environment
        self.Product = self.env["product.product"]
        self.Partner = self.env["res.partner"]

        # Create a product
        self.product = self.Product.create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
                "standard_price": 50.0,
            }
        )

        # Create a customer
        self.partner = self.Partner.create(
            {
                "name": "Test Customer",
                "email": "customer@example.com",
            }
        )

    def test_onchange_product_id_no_customer(self):
        # Create a sale order without a customer
        so = Form(self.env["sale.order"])
        # Try to add a product to the sale order line without a customer
        with self.assertRaises(UserError):
            so.order_line.new()

    def test_onchange_product_id_customer(self):
        so = Form(self.env["sale.order"])
        so.partner_id = self.partner
        with so.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
