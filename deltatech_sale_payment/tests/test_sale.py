from unittest.mock import patch

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleOrderPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        # Create a partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "partner@example.com",
            }
        )

        # Create a product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "list_price": 100.0,
                "is_storable": True,
            }
        )

        # Create a sale order
        self.sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )

        # Create a payment provider
        self.provider = self.env["payment.provider"].create(
            {
                "name": "Test Provider",
                "code": "none",
                "is_published": True,
                "state": "test",
            }
        )
        self.payment_method = self.env["payment.method"].search([], limit=1)

    def test_01_compute_payment_without(self):
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "without", "Initial payment status should be 'without'")

    def test_02_action_payment_link(self):
        with patch(
            "odoo.addons.payment.models.payment_link_wizard.PaymentLinkWizard._get_additional_link_values",
            return_value={},
        ):
            payment_link_action = self.sale_order.action_payment_link()
            self.assertIn("url", payment_link_action, "Payment link action should return a URL")

    def test_03_sale_confirm_payment(self):
        # Create a sale.confirm.payment wizard
        wizard = (
            self.env["sale.confirm.payment"]
            .with_context(active_id=self.sale_order.id)
            .create(
                {
                    "provider_id": self.provider.id,
                    "payment_method_id": self.payment_method.id,
                    "amount": 100.0,
                    "payment_date": fields.Date.today(),
                }
            )
        )

        self.assertEqual(
            wizard.currency_id.id, self.sale_order.currency_id.id, "Currency should match the sale order's currency"
        )

        wizard.do_confirm()

        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "done", "Payment status should be 'done' after confirmation")
        self.assertEqual(self.sale_order.payment_amount, 100.0)

    def test_04_invalid_confirm_payment(self):
        with self.assertRaises(UserError):
            wizard = (
                self.env["sale.confirm.payment"]
                .with_context(active_id=self.sale_order.id)
                .create(
                    {
                        "provider_id": self.provider.id,
                        "payment_method_id": self.payment_method.id,
                        "amount": -100.0,
                        "payment_date": fields.Date.today(),
                    }
                )
            )
            wizard.do_confirm()

    def test_05_default_get(self):
        wizard_vals = (
            self.env["sale.confirm.payment"].with_context(active_id=self.sale_order.id).default_get(["currency_id"])
        )
        self.assertEqual(
            wizard_vals["currency_id"],
            self.sale_order.currency_id.id,
            "Default currency should match the sale order's currency",
        )

    def test_06_partial_payment(self):
        wizard = (
            self.env["sale.confirm.payment"]
            .with_context(active_id=self.sale_order.id)
            .create(
                {
                    "provider_id": self.provider.id,
                    "payment_method_id": self.payment_method.id,
                    "amount": 50.0,
                    "payment_date": fields.Date.today(),
                }
            )
        )
        wizard.do_confirm()
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "partial")

    def test_07_initiated_payment(self):
        self.env["payment.transaction"].create(
            {
                "amount": 100.0,
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "partner_id": self.partner.id,
                "sale_order_ids": [(4, self.sale_order.id)],
                "currency_id": self.sale_order.currency_id.id,
                "state": "draft",
            }
        )
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "initiated")

    def test_08_authorized_payment(self):
        self.env["payment.transaction"].create(
            {
                "amount": 100.0,
                "provider_id": self.provider.id,
                "payment_method_id": self.payment_method.id,
                "partner_id": self.partner.id,
                "sale_order_ids": [(4, self.sale_order.id)],
                "currency_id": self.sale_order.currency_id.id,
                "state": "authorized",
            }
        )
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "authorized")
