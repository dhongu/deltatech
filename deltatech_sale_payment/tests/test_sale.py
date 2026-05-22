from datetime import date

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestSaleOrderPayment(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Partner",
                "email": "partner@example.com",
            }
        )

        self.product = self.env["product.product"].search([("sale_ok", "=", True), ("active", "=", True)], limit=1)
        if not self.product:
            self.skipTest("Nu există niciun produs de vânzare în baza de date de test")

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

        self.payment_journal = self.env["account.journal"].create(
            {
                "name": "Test Journal",
                "type": "bank",
                "code": "TJ",
            }
        )

        self.payment_method = self.env["payment.method"].search([], limit=1)
        if not self.payment_method:
            self.payment_method = self.env["payment.method"].create(
                {
                    "name": "Manual",
                    "code": "manual",
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
        self.sale_order.write({"transaction_ids": [(4, tx.id)]})
        return tx

    def test_compute_payment_without(self):
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "without")
        self.assertEqual(self.sale_order.payment_amount, 0.0)

    def test_compute_payment_pending(self):
        # Tranzacție pending → status "pending"
        self._create_transaction(amount=100.0, state="pending")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "pending")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider)

    def test_compute_payment_initiated(self):
        # Tranzacție draft/error (nu pending, nu done) → status "initiated"
        self._create_transaction(amount=10.0, state="error")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "initiated")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider)

    def test_compute_payment_authorized(self):
        self._create_transaction(amount=20.0, state="authorized")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "authorized")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        self.assertEqual(self.sale_order.provider_id, self.provider)

    def test_compute_payment_cancelled(self):
        self._create_transaction(amount=10.0, state="cancel")
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "cancelled")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        # Providerul este vizibil și pentru tranzacții anulate
        self.assertEqual(self.sale_order.provider_id, self.provider)

    def test_compute_payment_multiple_pending_and_error(self):
        # pending suprascrie error în ordinea priorității
        self._create_transaction(amount=10.0, state="error", provider=self.provider)
        self._create_transaction(amount=5.0, state="pending", provider=self.provider2)
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "pending")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        # Provider din ultima tranzacție pending (by id)
        self.assertEqual(self.sale_order.provider_id, self.provider2)

    def test_compute_payment_authorized_overrides_pending(self):
        # authorized are prioritate față de pending și cancel
        self._create_transaction(amount=10.0, state="pending", provider=self.provider)
        self._create_transaction(amount=20.0, state="authorized", provider=self.provider)
        self._create_transaction(amount=30.0, state="authorized", provider=self.provider2)
        self._create_transaction(amount=1.0, state="pending", provider=self.provider)
        self.sale_order._compute_payment()
        self.assertEqual(self.sale_order.payment_status, "authorized")
        self.assertEqual(self.sale_order.payment_amount, 0.0)
        # Provider din ultima tranzacție authorized (by id)
        self.assertEqual(self.sale_order.provider_id, self.provider2)

    def test_invalid_confirm_payment(self):
        with self.assertRaises(UserError):
            wizard = (
                self.env["sale.confirm.payment"]
                .with_context(active_id=self.sale_order.id)
                .create(
                    {
                        "provider_id": self.provider.id,
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
        )
