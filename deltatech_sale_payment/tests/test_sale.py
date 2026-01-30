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

        # Minimal payment provider and method for creating transactions
        # Reuse an existing payment method if available to avoid required image hassle
        self.payment_method = self.env["payment.method"].search([], limit=1)
        if not self.payment_method:
            self.payment_method = self.env["payment.method"].create(
                {
                    "name": "Manual",
                    "code": "manual",
                    # image is required; any valid non-empty base64 string works for tests
                    "image": "R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7",
                }
            )

        self.provider = self.env["payment.provider"].create(
            {
                "name": "Test Provider",
                "code": "none",
                "state": "enabled",
                "payment_method_ids": [(6, 0, [self.payment_method.id])],
                "capture_manually": True,
            }
        )
        self.provider.support_manual_capture = "full_only"

        # A second provider to test provider selection among multiple transactions
        self.provider2 = self.env["payment.provider"].create(
            {
                "name": "Test Provider 2",
                "code": "none",
                "state": "enabled",
                "payment_method_ids": [(6, 0, [self.payment_method.id])],
                "capture_manually": True,
            }
        )
        self.provider2.support_manual_capture = "full_only"

    def test_compute_payment(self):
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "without", "Initial payment status should be 'without'")

    def _create_transaction(self, *, amount, state, provider=None):
        tx_count = len(self.sale_order.transaction_ids)
        reference = f"TX-REF-{self.sale_order.id}-{tx_count}"
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": (provider or self.provider).id,
                "payment_method_id": self.payment_method.id,
                "reference": reference,
                "amount": amount,
                "currency_id": self.sale_order.currency_id.id,
                "state": state,
                "partner_id": self.partner.id,
            }
        )
        # Link transaction to sale order
        self.sale_order.write({"transaction_ids": [(4, tx.id)]})
        return tx

    def test_compute_payment_initiated(self):
        # Create a non-done transaction (pending) -> initiated status
        self._create_transaction(amount=10.0, state="pending")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "initiated")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider)

    def test_compute_payment_authorized(self):
        # Authorized transaction with no captured amount yet
        self._create_transaction(amount=20.0, state="authorized")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "authorized")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider)

        # Clean transactions for next assertions
        self.sale_order.write({"transaction_ids": [(5, 0, 0)]})

    # def test_compute_payment_partial_and_done(self):
    #     # Partial: done transaction less than order total
    #     self._create_transaction(amount=50.0, state="done", provider=self.provider)
    #     self.sale_order._compute_payment()
    #     self.assertEqual(self.sale_order.payment_status, "partial")
    #     self.assertEqual(self.sale_order.payment_amount, 50.0)
    #     self.assertEqual(self.sale_order.provider_id, self.provider)
    #
    #     # Add another done transaction to reach/exceed total -> done
    #     self._create_transaction(amount=60.0, state="done", provider=self.provider2)
    #     self.sale_order._compute_payment()
    #     self.assertEqual(self.sale_order.payment_status, "done")
    #     self.assertAlmostEqual(self.sale_order.payment_amount, 110.0)
    #     # Provider should be from the last done transaction (by id)
    #     self.assertEqual(self.sale_order.provider_id, self.provider2)
    #
    #     # Add a later pending transaction with yet another provider – should not override when amount>0
    #     provider3 = self.env["payment.provider"].create(
    #         {
    #             "name": "Test Provider 3",
    #             "code": "none",
    #             "state": "enabled",
    #             "payment_method_ids": [(6, 0, [self.payment_method.id])],
    #         }
    #     )
    #     self._create_transaction(amount=0.0, state="pending", provider=provider3)
    #     self.sale_order._compute_payment()
    #     self.assertEqual(self.sale_order.payment_status, "done")
    #     # Provider remains the one from the last done transaction
    #     self.assertEqual(self.sale_order.provider_id, self.provider2)

    def test_compute_payment_multiple_transactions_initiated_provider_from_last_by_id(self):
        # Two non-done transactions with different providers -> initiated, provider from the last tx by id
        self._create_transaction(amount=10.0, state="pending", provider=self.provider)
        self._create_transaction(amount=5.0, state="error", provider=self.provider2)
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "initiated")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider2)

    def test_compute_payment_multiple_transactions_authorized_provider_from_last_authorized(self):
        # Mix of states: last overall is pending, but there are authorized ones -> status authorized
        # Provider must be that of the last authorized transaction by id
        self._create_transaction(amount=10.0, state="pending", provider=self.provider)
        self._create_transaction(amount=20.0, state="authorized", provider=self.provider)
        self._create_transaction(amount=30.0, state="authorized", provider=self.provider2)
        self._create_transaction(amount=1.0, state="pending", provider=self.provider)

        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "authorized")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        # Provider should be from the last authorized transaction
        self.assertEqual(self.sale_order.provider_id, self.provider2)

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
    #         'provider_id': self.env['payment.provider'].create({'name': 'Test Provider'}).id,
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
