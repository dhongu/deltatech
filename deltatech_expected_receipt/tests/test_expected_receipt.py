# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Încasarea cu cardul și decontarea ei.

Cifra de aur vine din extrasul real pe care s-a construit fluxul:
3.519,03 = 301,59 + 33,17 + 3.184,27.
"""

import time
from datetime import date, timedelta

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon

GOLDEN = (301.59, 33.17, 3184.27)
GOLDEN_TOTAL = 3519.03


@tagged("post_install", "-at_install")
class TestExpectedReceipt(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.journal = cls.env["account.journal"].create(
            {"name": "ING POS", "code": "INGP", "type": "bank", "company_id": cls.company.id}
        )
        cls.suspense = cls.journal.suspense_account_id
        cls.suspense.reconcile = True
        cls.cashier = cls._user(
            "cashier",
            [
                "deltatech_expected_receipt.group_cashier",
                "sales_team.group_sale_manager",
                "account.group_account_readonly",
            ],
        )
        cls.manager = cls._user(
            "manager", ["deltatech_expected_receipt.group_manager", "account.group_account_manager"]
        )
        cls.terminal = cls.env["deltatech.card.terminal"].create(
            {"name": "ING Shop", "user_id": cls.cashier.id, "journal_id": cls.journal.id}
        )
        cls.partners = cls.env["res.partner"].create([{"name": "Glassmart"}, {"name": "Mansoor"}, {"name": "Davinox"}])
        cls.day = date(2026, 8, 21)

    @classmethod
    def _user(cls, login, groups):
        return cls.env["res.users"].create(
            {
                "name": login.title(),
                "login": f"er_{login}",
                "email": f"{login}@example.com",
                "company_id": cls.company.id,
                "company_ids": [Command.set(cls.company.ids)],
                "group_ids": [Command.set([cls.env.ref(xmlid).id for xmlid in ["base.group_user", *groups]])],
            }
        )

    # ------------------------------------------------------------------
    def _pay(self, partner=None, amount=100.0, day=None, user=None, record=None, **values):
        """Încasare prin dialog, ca în realitate (plată + rând în registru)."""
        user = user or self.manager
        context = {"active_model": record._name, "active_id": record.id} if record else {}
        with Form(self.env["deltatech.card.payment"].with_user(user).with_context(**context)) as form:
            if not record:
                form.partner_id = partner
            form.amount = amount
            form.date = day or self.day
            form.terminal_id = self.terminal
            for name, value in values.items():
                setattr(form, name, value)
        form.record.action_confirm()
        return self.env["deltatech.expected.receipt"].search([], order="id desc", limit=1)

    def _statement_line(self, amount, day=None):
        return self.env["account.bank.statement.line"].create(
            {"journal_id": self.journal.id, "date": day or self.day, "payment_ref": "ING POS", "amount": amount}
        )

    def _settlement(self, statement_line):
        wizard = (
            self.env["deltatech.card.settlement"]
            .with_user(self.manager)
            .create({"statement_line_id": statement_line.id, "company_id": self.company.id})
        )
        wizard.action_search()
        return wizard

    def _golden_receipts(self):
        return self.env["deltatech.expected.receipt"].concat(
            *[
                self._pay(partner, amount, self.day - timedelta(days=offset))
                for partner, amount, offset in zip(self.partners, GOLDEN, (1, 2, 3), strict=True)
            ]
        )

    # ------------------------------------------------------------------
    def test_card_payment_waits_on_5125(self):
        """Încasarea pe client: Dr 5125 = Cr 4111, rândul stă în așteptare."""
        receipt = self._pay(self.partners[0], 250.0)
        self.assertEqual(receipt.state, "pending")
        self.assertEqual(receipt.terminal_id, self.terminal)
        lines = receipt.payment_id.move_id.line_ids
        self.assertEqual(lines.filtered(lambda line: line.debit).account_id, self.suspense)
        self.assertEqual(
            lines.filtered(lambda line: line.credit).account_id, self.partners[0].property_account_receivable_id
        )

    def test_golden_figure_single_combination(self):
        receipts = self._golden_receipts()
        noise = self._pay(self.partners[0], 999.99, self.day - timedelta(days=1))
        statement_line = self._statement_line(GOLDEN_TOTAL)
        wizard = self._settlement(statement_line)
        self.assertEqual(wizard.state, "proposed")
        self.assertEqual(wizard.line_ids.filtered("selected").receipt_id, receipts)
        self.assertTrue(wizard.can_settle)
        wizard.action_settle()
        self.assertEqual(set(receipts.mapped("state")), {"settled"})
        self.assertEqual(receipts.statement_line_id, statement_line)
        self.assertTrue(statement_line.is_reconciled)
        self.assertEqual(noise.state, "pending")

    def test_two_combinations_are_not_chosen(self):
        self._pay(self.partners[0], 120.0)
        self._pay(self.partners[1], 80.0)
        self._pay(self.partners[2], 40.0)
        wizard = self._settlement(self._statement_line(120.0))
        self.assertEqual(wizard.state, "ambiguous")
        self.assertFalse(wizard.line_ids.filtered("selected"))
        self.assertFalse(wizard.can_settle)

    def test_equal_amounts_are_one_combination(self):
        """Două încasări egale de la clienți diferiți nu fac două variante distincte de sumă."""
        self._pay(self.partners[0], 50.0)
        self._pay(self.partners[1], 50.0)
        wizard = self._settlement(self._statement_line(100.0))
        self.assertEqual(wizard.state, "proposed")

    def test_no_exact_combination_is_not_settled(self):
        """Comisionul vine pe o linie separată: o diferență înseamnă grup greșit."""
        self._golden_receipts()
        statement_line = self._statement_line(GOLDEN_TOTAL - 10.0)
        wizard = self._settlement(statement_line)
        self.assertEqual(wizard.state, "manual")
        self.assertFalse(wizard.can_settle)
        wizard.line_ids.selected = True
        with self.assertRaises(UserError):
            wizard.action_settle()
        self.assertFalse(statement_line.is_reconciled)

    def test_window_stops_at_four_days(self):
        old = self._pay(self.partners[0], 70.0, self.day - timedelta(days=5))
        recent = self._pay(self.partners[1], 30.0, self.day - timedelta(days=4))
        wizard = self._settlement(self._statement_line(30.0))
        self.assertIn(recent, wizard.line_ids.receipt_id)
        self.assertNotIn(old, wizard.line_ids.receipt_id)

    def test_payment_on_invoice_reduces_residual(self):
        invoice = self.init_invoice("out_invoice", partner=self.partners[0], amounts=[1000.0], post=True)
        total = invoice.amount_total
        receipt = self._pay(amount=400.0, record=invoice, user=self.cashier)
        self.assertEqual(receipt.invoice_id, invoice)
        self.assertAlmostEqual(invoice.amount_residual, total - 400.0)

    def test_payment_on_order_issues_downpayment_invoice(self):
        """Pe o comandă nefacturată se emite factura de avans și se încasează pe ea."""
        order = (
            self.env["sale.order"]
            .with_user(self.cashier)
            .create(
                {
                    "partner_id": self.partners[0].id,
                    "order_line": [Command.create({"product_id": self.product_a.id, "product_uom_qty": 2})],
                }
            )
        )
        order.action_confirm()
        receipt = self._pay(amount=121.0, record=order, user=self.cashier)
        invoice = receipt.invoice_id
        self.assertTrue(invoice)
        self.assertEqual(invoice.state, "posted")
        self.assertIn(invoice, order.invoice_ids)
        self.assertAlmostEqual(invoice.amount_total, 121.0)
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))

    def test_cashier_cannot_skip_downpayment_invoice(self):
        order = (
            self.env["sale.order"]
            .with_user(self.cashier)
            .create(
                {"partner_id": self.partners[0].id, "order_line": [Command.create({"product_id": self.product_a.id})]}
            )
        )
        order.action_confirm()
        with self.assertRaises(UserError):
            self._pay(amount=50.0, record=order, user=self.cashier, invoice_mode="none")

    def test_user_without_group_cannot_pay(self):
        outsider = self._user("outsider", ["account.group_account_invoice"])
        with self.assertRaises(AccessError):
            self._pay(self.partners[0], 10.0, user=outsider)

    def test_cashier_cannot_change_the_register(self):
        receipt = self._pay(self.partners[0], 10.0, user=self.cashier)
        with self.assertRaises(AccessError):
            receipt.with_user(self.cashier).write({"state": "settled"})
        with self.assertRaises(AccessError):
            receipt.with_user(self.cashier).action_cancel()

    def test_card_receipt_without_payment_is_refused(self):
        with self.assertRaises(ValidationError):
            self.env["deltatech.expected.receipt"].sudo().create(
                {"partner_id": self.partners[0].id, "amount": 10.0, "terminal_id": self.terminal.id}
            )

    def test_cancel_cancels_the_payment(self):
        receipt = self._pay(self.partners[0], 10.0)
        receipt.with_user(self.manager).action_cancel()
        self.assertEqual(receipt.state, "cancelled")
        self.assertEqual(receipt.payment_id.state, "canceled")

    def test_cron_catches_reconciliation_done_elsewhere(self):
        receipt = self._pay(self.partners[0], 75.0)
        statement_line = self._statement_line(75.0)
        _liquidity, suspense, _other = statement_line._seek_for_lines()
        (suspense | receipt._settlement_lines()).reconcile()
        self.env["deltatech.expected.receipt"]._cron_sync_settlements()
        self.assertEqual(receipt.state, "settled")
        self.assertEqual(receipt.settlement_date, self.day)

    def test_late_filter(self):
        today = date.today()
        late = self._pay(self.partners[0], 10.0, today - timedelta(days=5))
        fresh = self._pay(self.partners[1], 20.0, today - timedelta(days=1))
        found = self.env["deltatech.expected.receipt"].search([("is_late", "=", True)])
        self.assertIn(late, found)
        self.assertNotIn(fresh, found)
        self.assertTrue(late.is_late)

    def test_one_terminal_per_user(self):
        with self.assertRaises(ValidationError):
            self.env["deltatech.card.terminal"].create(
                {"name": "Second", "user_id": self.cashier.id, "journal_id": self.journal.id}
            )

    def test_subset_sum_sixty_candidates_is_fast(self):
        Receipt = self.env["deltatech.expected.receipt"]
        items = [(1000 + 37 * index, Receipt) for index in range(60)]
        target = sum(value for value, _receipt in items[::3])
        start = time.perf_counter()
        chosen = Receipt._subset_sum(items, target)
        self.assertLess(time.perf_counter() - start, 1.0)
        self.assertEqual(sum(items[i][0] for i in chosen), target)

    def test_payment_on_quotation_confirms_the_order(self):
        """Clientul plătește oferta: comanda se confirmă și avansul se facturează."""
        order = (
            self.env["sale.order"]
            .with_user(self.cashier)
            .create(
                {"partner_id": self.partners[1].id, "order_line": [Command.create({"product_id": self.product_a.id})]}
            )
        )
        self.assertEqual(order.state, "draft")
        receipt = self._pay(amount=60.5, record=order, user=self.cashier)
        self.assertEqual(order.state, "sale")
        self.assertAlmostEqual(receipt.invoice_id.amount_total, 60.5)
        self.assertEqual(receipt.sale_order_id, order)
