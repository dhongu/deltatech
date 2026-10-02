from odoo import Command, fields
from odoo.tests import TransactionCase


class TestWeightCalculation(TransactionCase):
    def setUp(self):
        super().setUp()
        # Set up any necessary records or configurations
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "weight": 1.5,  # 1.5 Kg per unit
                "l10n_ro_net_weight": 1.2,  # 1.2 Kg per unit
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
        self.assertEqual(invoice.weight, 15.0, "Gross weight should be 15 Kg (1.5 Kg * 10)")
        self.assertAlmostEqual(invoice.weight_net, 12.0, msg="Net weight should be 12 Kg (1.2 Kg * 10)")

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
        self.assertEqual(purchase_order.weight_gross, 15.0, "Gross weight should be 15 Kg (1.5 Kg * 10)")
        self.assertAlmostEqual(purchase_order.weight_net, 12.0, msg="Net weight should be 12 Kg (1.2 Kg * 10)")

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
        self.assertEqual(sale_order.weight_gross, 15.0, "Gross weight should be 15 Kg (1.5 Kg * 10)")
        self.assertAlmostEqual(sale_order.weight_net, 12.0, msg="Net weight should be 12 Kg (1.2 Kg * 10)")

    def test_invoice_report_shows_weight(self):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "quantity": 10,
                            "price_unit": 100,
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        self.assertTrue(invoice.payment_reference)
        html, _report_type = self.env["ir.actions.report"]._render_qweb_html("account.account_invoices", invoice.ids)
        html = html.decode()
        self.assertIn("Gross weight:", html)
        self.assertIn("15", html)
