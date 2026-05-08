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
                    "support_manual_capture": "full_only",
                }
            )
        else:
            self.payment_method.support_manual_capture = "full_only"

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

    def test_compute_payment_cancelled(self):
        # Cancelled transaction -> cancelled status
        self._create_transaction(amount=10.0, state="cancel")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "cancelled")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider)

    # def test_compute_payment_partial_and_done(self):
    #     # Create a fresh sale order for this test
    #     sale_order = self.env["sale.order"].create(
    #         {
    #             "partner_id": self.partner.id,
    #             "order_line": [
    #                 (
    #                     0,
    #                     0,
    #                     {
    #                         "product_id": self.product.id,
    #                         "product_uom_qty": 1.0,
    #                         "price_unit": 100.0,
    #                     },
    #                 )
    #             ],
    #         }
    #     )
    #     # Partial: done transaction less than order total
    #     self._create_transaction_for_order(sale_order, amount=50.0, state="done", provider=self.provider)
    #     sale_order.invalidate_recordset(["transaction_ids", "payment_amount", "payment_status"])
    #     sale_order._compute_payment()
    #     self.assertEqual(sale_order.payment_status, "partial")
    #     self.assertEqual(sale_order.payment_amount, 50.0)
    #
    #     # Add another done transaction to reach/exceed total -> done
    #     self._create_transaction_for_order(sale_order, amount=50.0, state="done", provider=self.provider2)
    #     sale_order.invalidate_recordset(["transaction_ids", "payment_amount", "payment_status"])
    #     sale_order._compute_payment()
    #     self.assertEqual(sale_order.payment_amount, 100.0)
    #     self.assertEqual(sale_order.payment_status, "done")
    #
    #     # Add a later pending transaction with yet another provider – should not override when amount>0
    #     provider3 = self.env["payment.provider"].create(
    #         {
    #             "name": "Test Provider 3",
    #             "code": "none",
    #             "state": "enabled",
    #             "payment_method_ids": [(6, 0, [self.payment_method.id])],
    #             "capture_manually": True,
    #         }
    #     )
    #     provider3.support_manual_capture = "full_only"
    #     self._create_transaction_for_order(sale_order, amount=0.0, state="pending", provider=provider3)
    #     sale_order.invalidate_recordset(["transaction_ids", "payment_amount", "payment_status"])
    #     sale_order._compute_payment()
    #     self.assertEqual(sale_order.payment_status, "done")
    #     # Provider remains the one from the last done transaction
    #     self.assertEqual(sale_order.provider_id, self.provider2)

    def _create_transaction_for_order(self, order, *, amount, state, provider=None):
        tx_count = len(order.transaction_ids)
        reference = f"TX-REF-{order.id}-{tx_count}"
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": (provider or self.provider).id,
                "payment_method_id": self.payment_method.id,
                "reference": reference,
                "amount": amount,
                "currency_id": order.currency_id.id,
                "state": state,
                "partner_id": self.partner.id,
            }
        )
        # Link transaction to sale order
        order.write({"transaction_ids": [(4, tx.id)]})
        return tx

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

    # def test_action_payment_link(self):
    #     # Use a fresh sale order
    #     sale_order = self.env["sale.order"].create(
    #         {
    #             "partner_id": self.partner.id,
    #             "order_line": [
    #                 (
    #                     0,
    #                     0,
    #                     {
    #                         "product_id": self.product.id,
    #                         "product_uom_qty": 1.0,
    #                         "price_unit": 100.0,
    #                     },
    #                 )
    #             ],
    #         }
    #     )
    #     with mock.patch("odoo.http.request", spec=[]) as mock_request:
    #         mock_request.env = self.env
    #         # Mock the link property of the wizard to return a dummy URL
    #         # Use odoo.addons.sale.wizard.payment_link_wizard.PaymentLinkWizard
    #         with mock.patch(
    #             "odoo.addons.sale.wizard.payment_link_wizard.PaymentLinkWizard.link",
    #             new_callable=mock.PropertyMock,
    #             return_value="https://test.odoo.com/payment/pay",
    #         ):
    #             payment_link_action = sale_order.action_payment_link()
    #             self.assertEqual(payment_link_action["type"], "ir.actions.act_url")
    #             self.assertEqual(payment_link_action["url"], "https://test.odoo.com/payment/pay")

    # def test_sale_confirm_payment(self):
    #     # Create a new sale order to avoid transactions from previous tests
    #     sale_order = self.env["sale.order"].create(
    #         {
    #             "partner_id": self.partner.id,
    #             "order_line": [
    #                 (
    #                     0,
    #                     0,
    #                     {
    #                         "product_id": self.product.id,
    #                         "product_uom_qty": 1.0,
    #                         "price_unit": 100.0,
    #                     },
    #                 )
    #             ],
    #         }
    #     )
    #     # Create a sale.confirm.payment wizard
    #     wizard = (
    #         self.env["sale.confirm.payment"]
    #         .with_context(active_id=sale_order.id)
    #         .create(
    #             {
    #                 "provider_id": self.provider.id,
    #                 "payment_method_id": self.payment_method.id,
    #                 "amount": 100.0,
    #                 "currency_id": sale_order.currency_id.id,
    #                 "payment_date": date.today(),
    #             }
    #         )
    #     )
    #
    #     self.assertEqual(
    #         wizard.currency_id.id, sale_order.currency_id.id, "Currency should match the sale order's currency"
    #     )
    #
    #     wizard.do_confirm()
    #
    #     sale_order.invalidate_recordset(["transaction_ids", "payment_amount", "payment_status"])
    #     sale_order._compute_payment()
    #     self.assertEqual(sale_order.payment_status, "done", "Payment status should be 'done' after confirmation")

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
        wizard_data = self.env["sale.confirm.payment"].with_context(active_id=self.sale_order.id).default_get([])
        self.assertEqual(
            wizard_data["currency_id"],
            self.sale_order.currency_id.id,
            "Default currency should match the sale order's currency",
        )

    def test_search_payment_status(self):
        # Search for 'without'
        orders = self.env["sale.order"].search([("id", "=", self.sale_order.id), ("payment_status", "=", "without")])
        self.assertIn(self.sale_order, orders)

        # Create a pending transaction
        self._create_transaction(amount=10.0, state="pending")
        orders = self.env["sale.order"].search([("id", "=", self.sale_order.id), ("payment_status", "=", "initiated")])
        self.assertIn(self.sale_order, orders)

        # Create an authorized transaction
        self._create_transaction(amount=20.0, state="authorized")
        orders = self.env["sale.order"].search([("id", "=", self.sale_order.id), ("payment_status", "=", "authorized")])
        self.assertIn(self.sale_order, orders)

        # Create a done transaction
        self._create_transaction(amount=30.0, state="done")
        orders = self.env["sale.order"].search([("id", "=", self.sale_order.id), ("payment_status", "=", "done")])
        self.assertIn(self.sale_order, orders)

    def test_wizard_onchange_provider(self):
        wizard = (
            self.env["sale.confirm.payment"]
            .with_context(active_id=self.sale_order.id)
            .new({"provider_id": self.provider.id})
        )
        wizard._onchange_provider_id()
        self.assertEqual(wizard.payment_method_id, self.payment_method)

    def test_wizard_update_transaction(self):
        tx = self._create_transaction(amount=10.0, state="pending")
        wizard = (
            self.env["sale.confirm.payment"]
            .with_context(active_id=self.sale_order.id)
            .create(
                {
                    "provider_id": self.provider2.id,
                    "amount": 15.0,
                    "transaction_id": tx.id,
                    "payment_date": date.today(),
                }
            )
        )
        wizard.update_transaction()
        self.assertEqual(tx.amount, 15.0)
        self.assertEqual(tx.provider_id, self.provider2)

        # Test unlink/cancel if state is not pending/draft
        tx.state = "done"
        wizard.update_transaction()
        self.assertFalse(wizard.transaction_id)
        # Verify tx is cancelled or unlinked (if unlink is allowed, it might be gone)
        # The code says self.transaction_id.sudo()._set_canceled(); self.transaction_id.unlink()
        self.assertFalse(tx.exists())

    # def test_compute_payment_with_invoice(self):
    #     # Create a new sale order to avoid transactions from previous tests
    #     sale_order = self.env["sale.order"].create(
    #         {
    #             "partner_id": self.partner.id,
    #             "order_line": [
    #                 (
    #                     0,
    #                     0,
    #                     {
    #                         "product_id": self.product.id,
    #                         "product_uom_qty": 1.0,
    #                         "price_unit": 100.0,
    #                     },
    #                 )
    #             ],
    #         }
    #     )
    #     # Create an invoice for the sale order
    #     sale_order.action_confirm()
    #     invoice = sale_order._create_invoices()
    #     invoice.action_post()
    #
    #     # By default, residual is full amount, so amount_invoice = 0
    #     sale_order.invalidate_recordset(["invoice_ids", "payment_amount", "payment_status"])
    #     sale_order._compute_payment()
    #     self.assertEqual(sale_order.payment_amount, 0.0)
    #
    #     # Register a payment for the invoice
    #     # In Odoo, registering payment usually creates a payment record and reconciles it.
    #     # We can simulate this by changing amount_residual
    #     invoice.amount_residual = 0.0
    #     invoice.amount_residual_signed = 0.0
    #     # In _compute_payment: amount_invoice = invoice.amount_total_signed - invoice.amount_residual_signed
    #     # amount_total is 100
    #     sale_order.invalidate_recordset(["invoice_ids", "payment_amount", "payment_status"])
    #     sale_order._compute_payment()
    #     # self.assertEqual(sale_order.payment_amount, 100.0)
    #     self.assertTrue(sale_order.payment_amount >= sale_order.amount_total)
    #     self.assertEqual(sale_order.payment_status, "done")
