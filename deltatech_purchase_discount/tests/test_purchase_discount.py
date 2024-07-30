from odoo.tests.common import TransactionCase


class TestPurchaseOrderLine(TransactionCase):

    def setUp(self):
        super().setUp()

        # Create a company with purchase_keep_discount set to True
        self.company = self.env["res.company"].create(
            {
                "name": "Test Company",
                "purchase_keep_discount": True,
            }
        )

        # Create a purchase order
        self.purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.env.ref("base.res_partner_1").id,
                "company_id": self.company.id,
            }
        )

        # Create a purchase order line
        self.purchase_order_line = self.env["purchase.order.line"].create(
            {
                "order_id": self.purchase_order.id,
                "product_id": self.env.ref("product.product_product_8").id,
                "product_qty": 10.0,
                "product_uom": self.env.ref("uom.product_uom_unit").id,
                "price_unit": 100.0,
                "discount_received": 10.0,
                "price_without_discount": 100.0,
            }
        )

    def test_onchange_discount(self):
        # Call the onchange_discount method
        self.purchase_order_line.onchange_discount()

        # Check the price_unit field
        self.assertEqual(self.purchase_order_line.price_unit, 90.0, "The price_unit field should be 90.0")

    def test_prepare_account_move_line(self):
        # Call the _prepare_account_move_line method
        res = self.purchase_order_line._prepare_account_move_line()

        # Check the discount and price_unit fields
        self.assertEqual(res["discount"], 10.0, "The discount field should be 10.0")
        self.assertEqual(res["price_unit"], 100.0, "The price_unit field should be 100.0")
