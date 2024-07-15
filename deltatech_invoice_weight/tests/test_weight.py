from odoo import fields
from odoo.tests import TransactionCase


class TestWeightCalculation(TransactionCase):

    def setUp(self):
        super().setUp()
        # Set up any necessary records or configurations
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "weight": 1.5,  # 1.5 Kg per unit
            }
        )
        # Create a partner for the tests
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

    def test_account_invoice_weight_calculation(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 10,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        # Check the net weight
        self.assertEqual(invoice.weight_net, 15.0, "Net weight should be 15 Kg (1.5 Kg * 10)")

    def test_purchase_order_weight_calculation(self):
        purchase_order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 10,
                            "price_unit": 100,
                            "date_planned": fields.Datetime.now(),
                        },
                    )
                ],
            }
        )
        # Check the net weight
        self.assertEqual(purchase_order.weight_net, 15.0, "Net weight should be 15 Kg (1.5 Kg * 10)")

    def test_sale_order_weight_calculation(self):
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 10,
                            "price_unit": 100,
                        },
                    )
                ],
            }
        )
        # Check the net weight
        self.assertEqual(sale_order.weight_net, 15.0, "Net weight should be 15 Kg (1.5 Kg * 10)")
