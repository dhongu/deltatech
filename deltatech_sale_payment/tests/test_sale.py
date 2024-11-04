from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


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

        # Create a payment journal
        self.payment_journal = self.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "bank",
                "code": "TJ",
            }
        )

    def test_compute_payment(self):
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "without", "Initial payment status should be 'without'")

    # @mock.patch('odoo.http.request', autospec=True)
    # def test_action_payment_link(self, mock_request):
    #     # Mock the environment for the request object
    #     mock_request.env = self.env
    #     mock_request.env.su = True
    #     mock_request.httprequest = mock.Mock()
    #
    #     payment_link_action = self.sale_order.action_payment_link()
    #     self.assertIn('url', payment_link_action, "Payment link action should return a URL")

    # def test_sale_confirm_payment(self):
    #     # Create a sale.confirm.payment wizard
    #     wizard = self.env['sale.confirm.payment'].with_context(active_id=self.sale_order.id).create({
    #         'acquirer_id': self.env['payment.provider'].create({'name': 'Test Provider'}).id,
    #         'amount': 100.0,
    #         'currency_id': self.env.ref('base.USD').id,
    #         'payment_date': date.today(),
    #     })
    #
    #     self.assertEqual(wizard.currency_id.id, self.sale_order.currency_id.id,
    #                      "Currency should match the sale order's currency")
    #
    #     # Set default journal in context to avoid null journal_id issue
    #     with self.env.cr.savepoint():
    #         wizard = wizard.with_context(default_journal_id=self.payment_journal.id)
    #         wizard.do_confirm()
    #
    #     self.sale_order._compute_payment()
    #     self.assertEqual(self.sale_order.payment_status, 'done', "Payment status should be 'done' after confirmation")

    def test_invalid_confirm_payment(self):
        with self.assertRaises(UserError):
            wizard = (
                self.env["sale.confirm.payment"]
                .with_context(active_id=self.sale_order.id)
                .create(
                    {
                        "provider_id": self.env["payment.provider"].create({"name": "Test Provider"}).id,
                        "amount": -100.0,
                        "currency_id": self.env.ref("base.USD").id,
                        "payment_date": date.today(),
                    }
                )
            )
            wizard.do_confirm()

    def test_default_get(self):
        wizard = self.env["sale.confirm.payment"].with_context(active_id=self.sale_order.id).default_get([])
        self.assertEqual(
            wizard["currency_id"],
            self.sale_order.currency_id.id,
            "Default currency should match the sale order's currency",
        )
