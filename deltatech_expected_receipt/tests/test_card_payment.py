# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Dialogul „Încasare cu cardul”: de unde se deschide, ce propune, ce avertizează și ce refuză."""

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from .common import ExpectedReceiptCommon


@tagged("post_install", "-at_install")
class TestCardPayment(ExpectedReceiptCommon):
    def _wizard(self, user=None, **values):
        values.setdefault("partner_id", self.partners[0].id)
        values.setdefault("terminal_id", self.terminal.id)
        values.setdefault("amount", 100.0)
        values.setdefault("date", self.day)
        return self.env["deltatech.card.payment"].with_user(user or self.manager).create(values)

    def _open(self, record, user=None):
        action = record.with_user(user or self.cashier).action_card_payment()
        return Form(
            self.env["deltatech.card.payment"].with_user(user or self.cashier).with_context(**action["context"])
        )

    # ------------------------------------------------------------------
    #  De unde se deschide și ce propune
    # ------------------------------------------------------------------
    def test_buttons_on_invoice_and_order(self):
        invoice = self.init_invoice("out_invoice", partner=self.partners[0], amounts=[500.0], post=True)
        order = self._order()
        for record in (invoice, order):
            action = record.action_card_payment()
            self.assertEqual(action["res_model"], "deltatech.card.payment")
            self.assertEqual(action["context"], {"active_model": record._name, "active_id": record.id})
        receipt = self._pay(amount=100.0, record=invoice)
        self.assertEqual(invoice.action_view_card_receipts()["domain"], [("invoice_id", "=", invoice.id)])
        self.assertEqual(order.action_view_card_receipts()["domain"], [("sale_order_id", "=", order.id)])
        self.assertEqual(self.env["deltatech.expected.receipt"].search([("invoice_id", "=", invoice.id)]), receipt)

    def test_invoice_proposes_its_residual(self):
        invoice = self.init_invoice("out_invoice", partner=self.partners[0], amounts=[500.0], post=True)
        form = self._open(invoice)
        self.assertEqual(form.invoice_mode, "invoice")
        self.assertEqual(form.partner_id, self.partners[0])
        self.assertAlmostEqual(form.amount, invoice.amount_residual)
        self.assertEqual(form.terminal_id, self.terminal, "the cashier's terminal is chosen automatically")
        form.amount = 200.0
        self.assertAlmostEqual(form.amount_left, invoice.amount_residual - 200.0)

    def test_invoiced_order_pays_the_open_invoice(self):
        """Comanda are deja factura emisă: dialogul plătește factura, fără factură de avans."""
        order = self._order()
        invoice = order._create_invoices()
        invoice.action_post()
        form = self._open(order)
        self.assertEqual(form.invoice_mode, "invoice")
        self.assertEqual(form.invoice_id, invoice)
        self.assertAlmostEqual(form.amount, invoice.amount_residual)
        form.save().action_confirm()
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        self.assertEqual(len(order.invoice_ids), 1)

    def test_order_amount_due_subtracts_unbilled_receipts(self):
        """Ce s-a încasat deja pe comandă, fără factură, nu se mai propune a doua oară."""
        order = self._order()
        self.assertAlmostEqual(order.amount_total, 1210.0)
        self._pay(amount=210.0, record=order, invoice_mode="none")
        form = self._open(order, user=self.manager)
        self.assertEqual(form.invoice_mode, "downpayment")
        self.assertAlmostEqual(form.amount_due, 1000.0)
        self.assertAlmostEqual(form.amount, 1000.0)
        form.amount = 1.0
        form.invoice_mode = "none"
        self.assertAlmostEqual(form.amount, 1000.0, "switching the mode proposes the remaining due again")
        self.assertFalse(form.invoice_id)

    def test_manager_registers_order_payment_without_invoice(self):
        """Doar managerul poate încasa pe comandă fără factură de avans; rândul primește o notă."""
        order = self._order()
        receipt = self._pay(amount=50.0, record=order, invoice_mode="none")
        self.assertFalse(receipt.invoice_id)
        self.assertEqual(receipt.sale_order_id, order)
        self.assertFalse(order.invoice_ids)
        self.assertIn("without a down payment invoice", "".join(receipt.message_ids.mapped("body")))
        self.assertTrue(receipt.has_document)
        self.assertEqual(receipt.document_name, order.name)

    # ------------------------------------------------------------------
    #  Avertismente
    # ------------------------------------------------------------------
    def test_warning_journal_without_suspense_account(self):
        journal = self.env["account.journal"].create({"name": "No suspense", "code": "NOSU", "type": "bank"})
        journal.suspense_account_id = False
        terminal = self.env["deltatech.card.terminal"].create({"name": "Bare", "journal_id": journal.id})
        wizard = self._wizard(terminal_id=terminal.id)
        self.assertIn("no suspense account", wizard.warning)
        with self.assertRaisesRegex(UserError, "no suspense account"):
            wizard.action_confirm()

    def test_warning_company_without_downpayment_account(self):
        self.company.downpayment_account_id = False
        wizard = self._wizard(sale_order_id=self._order().id, invoice_mode="downpayment")
        self.assertIn("Downpayment Account", wizard.warning)

    def test_warning_order_payment_without_invoice(self):
        wizard = self._wizard(sale_order_id=self._order().id, invoice_mode="none")
        self.assertIn("down payment invoice is required", wizard.warning)

    def test_warning_amount_over_due(self):
        wizard = self._wizard(amount=150.0, amount_due=100.0)
        self.assertIn("exceeds the amount due", wizard.warning)
        self.assertNotIn("On an order", wizard.warning)
        wizard = self._wizard(
            amount=150.0, amount_due=100.0, sale_order_id=self._order().id, invoice_mode="downpayment"
        )
        self.assertIn("On an order", wizard.warning)
        self.assertFalse(self._wizard(amount=50.0, amount_due=100.0).warning)

    # ------------------------------------------------------------------
    #  Refuzuri
    # ------------------------------------------------------------------
    def test_confirm_twice_is_refused(self):
        wizard = self._wizard()
        wizard.action_confirm()
        with self.assertRaisesRegex(UserError, "already been registered"):
            wizard.action_confirm()
        self.assertEqual(
            self.env["deltatech.expected.receipt"].search_count([("partner_id", "=", self.partners[0].id)]), 1
        )

    def test_document_of_another_customer_is_refused(self):
        invoice = self.init_invoice("out_invoice", partner=self.partners[0], amounts=[500.0], post=True)
        wizard = self._wizard(partner_id=self.partners[1].id, invoice_id=invoice.id, invoice_mode="invoice")
        with self.assertRaisesRegex(UserError, "does not belong to"):
            wizard.action_confirm()

    def test_cancelled_order_is_refused(self):
        order = self._order(confirm=False)
        order.action_cancel()
        wizard = self._wizard(sale_order_id=order.id, invoice_mode="downpayment")
        with self.assertRaisesRegex(UserError, "order is cancelled"):
            wizard.action_confirm()

    def test_invoice_mode_needs_a_posted_invoice(self):
        with self.assertRaisesRegex(UserError, "Select the invoice"):
            self._wizard(invoice_mode="invoice").action_confirm()
        draft = self.init_invoice("out_invoice", partner=self.partners[0], amounts=[500.0])
        with self.assertRaisesRegex(UserError, "posted customer invoice"):
            self._wizard(invoice_mode="invoice", invoice_id=draft.id).action_confirm()

    def test_downpayment_needs_an_order(self):
        with self.assertRaisesRegex(UserError, "issued from a sales order"):
            self._wizard(invoice_mode="downpayment").action_confirm()

    def test_zero_amount_is_refused(self):
        with self.assertRaisesRegex(UserError, "greater than zero"):
            self._wizard(amount=0.0).action_confirm()

    def test_suspense_account_must_allow_reconciliation(self):
        self.suspense.reconcile = False
        with self.assertRaisesRegex(UserError, "does not allow reconciliation"):
            self._wizard().action_confirm()
        self.assertFalse(self.env["deltatech.expected.receipt"].search([("partner_id", "=", self.partners[0].id)]))

    def test_company_outside_the_user_companies_is_refused(self):
        other = self.setup_other_company()["company"]
        journal = self.env["account.journal"].create(
            {"name": "Other POS", "code": "OPOS", "type": "bank", "company_id": other.id}
        )
        terminal = self.env["deltatech.card.terminal"].create(
            {"name": "Other", "journal_id": journal.id, "company_id": other.id}
        )
        wizard = (
            self.env["deltatech.card.payment"]
            .sudo()
            .create(
                {
                    "company_id": other.id,
                    "partner_id": self.partners[0].id,
                    "terminal_id": terminal.id,
                    "currency_id": other.currency_id.id,
                    "amount": 100.0,
                }
            )
        )
        with self.assertRaisesRegex(UserError, "not one of your companies"):
            wizard.with_user(self.manager).action_confirm()
