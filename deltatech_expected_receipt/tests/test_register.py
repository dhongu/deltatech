# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Registrul încasărilor așteptate și terminalele: anulare, sincronizare cu contabilitatea,
întârzieri, reguli de integritate."""

from datetime import date, timedelta
from unittest.mock import patch

from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged

from ..models.expected_receipt import ExpectedReceipt
from .common import ExpectedReceiptCommon


@tagged("post_install", "-at_install")
class TestRegister(ExpectedReceiptCommon):
    # ------------------------------------------------------------------
    #  Anulare
    # ------------------------------------------------------------------
    def test_settled_receipt_cannot_be_cancelled(self):
        receipt = self._pay(self.partners[0], 60.0)
        self._settlement(self._statement_line(60.0)).action_settle()
        with self.assertRaisesRegex(UserError, "already settled"):
            receipt.with_user(self.manager).action_cancel()

    def test_reconciled_payment_cannot_be_cancelled(self):
        """Contabilul a reconciliat din ecranul standard, iar cronul n-a trecut încă."""
        receipt = self._pay(self.partners[0], 60.0)
        self._reconcile_elsewhere(receipt, self._statement_line(60.0))
        self.assertEqual(receipt.state, "pending")
        with self.assertRaisesRegex(UserError, "already reconciled"):
            receipt.with_user(self.manager).action_cancel()

    def test_cancel_keeps_the_downpayment_invoice(self):
        """Factura de avans are TVA colectat: rămâne, iar rândul spune că trebuie stornată."""
        receipt = self._pay(amount=121.0, record=self._order(), user=self.cashier)
        invoice = receipt.invoice_id
        receipt.with_user(self.manager).action_cancel()
        self.assertEqual(receipt.state, "cancelled")
        self.assertEqual(invoice.state, "posted")
        self.assertIn("stays posted", "".join(receipt.message_ids.mapped("body")))

    # ------------------------------------------------------------------
    #  Sincronizarea cu contabilitatea
    # ------------------------------------------------------------------
    def test_payment_cancelled_in_accounting_cancels_the_receipt(self):
        receipt = self._pay(self.partners[0], 60.0)
        receipt.payment_id.action_cancel()
        receipt._sync_state_from_accounting()
        self.assertEqual(receipt.state, "cancelled")
        # Un rând anulat nu mai e atins de sincronizare.
        receipt._sync_state_from_accounting()
        self.assertEqual(receipt.state, "cancelled")

    def test_unreconcile_brings_the_receipt_back(self):
        receipt = self._pay(self.partners[0], 60.0)
        self._settlement(self._statement_line(60.0)).action_settle()
        self.assertEqual(receipt.state, "settled")
        receipt._settlement_lines(include_reconciled=True).remove_move_reconcile()
        # Cronul se uită doar la decontările din ultimele 30 de zile; ziua testului e mai veche.
        receipt._sync_state_from_accounting()
        self.assertEqual(receipt.state, "pending")
        self.assertFalse(receipt.settlement_date)
        self.assertFalse(receipt.statement_line_id)

    def test_cron_survives_a_failing_chunk(self):
        receipt = self._pay(self.partners[0], 60.0)
        with (
            patch.object(ExpectedReceipt, "_sync_state_from_accounting", side_effect=ValueError("boom")),
            self.assertLogs("odoo.addons.deltatech_expected_receipt.models.expected_receipt", "ERROR"),
        ):
            self.env["deltatech.expected.receipt"]._cron_sync_settlements()
        self.assertEqual(receipt.state, "pending")

    # ------------------------------------------------------------------
    #  Ecran, întârzieri, integritate
    # ------------------------------------------------------------------
    def test_open_document_and_payment(self):
        on_customer = self._pay(self.partners[0], 60.0)
        self.assertFalse(on_customer.has_document)
        self.assertFalse(on_customer.document_name)
        self.assertIn(self.partners[0].name, on_customer.name)
        with self.assertRaisesRegex(UserError, "without a document"):
            on_customer.action_open_document()
        self.assertEqual(on_customer.action_open_payment()["res_id"], on_customer.payment_id.id)
        invoice = self.init_invoice("out_invoice", partner=self.partners[0], amounts=[500.0], post=True)
        on_invoice = self._pay(amount=100.0, record=invoice)
        action = on_invoice.action_open_document()
        self.assertEqual((action["res_model"], action["res_id"]), ("account.move", invoice.id))
        self.assertEqual(on_invoice.document_name, invoice.name)

    def test_late_threshold_comes_from_the_terminal(self):
        today = date.today()
        patient = self.env["deltatech.card.terminal"].create(
            {"name": "Slow bank", "journal_id": self.journal.id, "late_days": 10}
        )
        Receipt = self.env["deltatech.expected.receipt"]
        default_late = self._pay(self.partners[0], 10.0, today - timedelta(days=5))
        patient_ok = self._pay(self.partners[1], 20.0, today - timedelta(days=5), terminal_id=patient)
        patient_late = self._pay(self.partners[2], 30.0, today - timedelta(days=11), terminal_id=patient)
        self.assertEqual(default_late.days_pending, 5)
        self.assertFalse(patient_ok.is_late)
        late = Receipt.search([("is_late", "=", True)])
        self.assertIn(default_late, late)
        self.assertIn(patient_late, late)
        self.assertNotIn(patient_ok, late)
        not_late = Receipt.search([("is_late", "=", False)])
        self.assertIn(patient_ok, not_late)
        self.assertNotIn(patient_late, not_late)
        self.assertEqual(Receipt.search([("is_late", "in", [True, False])]), Receipt.search([]))
        # O încasare decontată sau anulată nu mai e în întârziere.
        default_late.with_user(self.manager).action_cancel()
        self.assertEqual(default_late.days_pending, 0)
        self.assertFalse(default_late.is_late)

    def test_manager_corrects_but_amount_stays_positive(self):
        receipt = self._pay(self.partners[0], 60.0)
        receipt.with_user(self.manager).write({"note": "POS 1234", "date": self.day - timedelta(days=1)})
        self.assertEqual(receipt.note, "POS 1234")
        with self.assertRaises(ValidationError):
            receipt.with_user(self.manager).write({"amount": 0.0})

    def test_document_must_belong_to_the_customer(self):
        receipt = self._pay(self.partners[0], 60.0)
        invoice = self.init_invoice("out_invoice", partner=self.partners[1], amounts=[500.0], post=True)
        with self.assertRaisesRegex(ValidationError, "belongs to"):
            receipt.with_user(self.manager).write({"invoice_id": invoice.id})

    # ------------------------------------------------------------------
    #  Terminale
    # ------------------------------------------------------------------
    def test_terminal_receipts_and_settings(self):
        receipts = self._pay(self.partners[0], 10.0) | self._pay(self.partners[1], 20.0)
        self.assertEqual(self.terminal.receipt_count, 2)
        action = self.terminal.action_open_receipts()
        self.assertEqual(action["domain"], [("terminal_id", "=", self.terminal.id)])
        self.assertEqual(self.env["deltatech.expected.receipt"].search(action["domain"]), receipts)
        with self.assertRaises(ValidationError):
            self.terminal.late_days = -1

    def test_default_terminal(self):
        """Terminalul utilizatorului; altfel, singurul terminal al firmei; altfel, niciunul."""
        Terminal = self.env["deltatech.card.terminal"]
        self.assertEqual(Terminal._default_for_user(self.cashier), self.terminal)
        self.assertEqual(Terminal._default_for_user(self.manager), self.terminal)
        Terminal.create({"name": "Second", "journal_id": self.journal.id})
        self.assertFalse(Terminal._default_for_user(self.manager))
