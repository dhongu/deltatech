# ©  2026 Terrabit
# See README.rst file on addons root folder for license details
"""Decontarea: căutarea combinației, mesajele când nu iese și refuzurile la reconciliere."""

from datetime import timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from ..models.expected_receipt import MAX_CANDIDATES, MAX_TARGET_CENTS
from .common import ExpectedReceiptCommon


@tagged("post_install", "-at_install")
class TestCardSettlement(ExpectedReceiptCommon):
    def test_opened_from_the_statement_line(self):
        statement_line = self._statement_line(100.0)
        action = statement_line.action_card_settlement()
        self.assertEqual(action["res_model"], "deltatech.card.settlement")
        self.assertEqual(action["context"]["default_statement_line_id"], statement_line.id)

    # ------------------------------------------------------------------
    #  Căutarea
    # ------------------------------------------------------------------
    def test_search_needs_an_open_incoming_line(self):
        Settlement = self.env["deltatech.card.settlement"].with_user(self.manager)
        with self.assertRaisesRegex(UserError, "Select the bank statement line"):
            Settlement.create({"company_id": self.company.id}).action_search()
        with self.assertRaisesRegex(UserError, "incoming statement lines"):
            self._settlement(self._statement_line(-50.0))
        receipt = self._pay(self.partners[0], 75.0)
        statement_line = self._statement_line(75.0)
        self._reconcile_elsewhere(receipt, statement_line)
        with self.assertRaisesRegex(UserError, "already reconciled"):
            self._settlement(statement_line)

    def test_no_receipt_in_the_window(self):
        wizard = self._settlement(self._statement_line(100.0))
        self.assertEqual(wizard.state, "manual")
        self.assertIn("No pending card receipt", wizard.message)
        self.assertFalse(wizard.line_ids)

    def test_missing_amount_is_pointed_out(self):
        """Extrasul e mai mare decât tot ce așteaptă: lipsește o încasare."""
        self._pay(self.partners[0], 100.0)
        wizard = self._settlement(self._statement_line(150.0))
        self.assertEqual(wizard.state, "manual")
        self.assertIn("is missing", wizard.message)
        self.assertAlmostEqual(wizard.difference, 150.0)

    def test_terminal_filter_and_window(self):
        """Terminalul ales restrânge candidații și dă fereastra lui de căutare."""
        terminal = self.env["deltatech.card.terminal"].create(
            {"name": "ING Office", "journal_id": self.journal.id, "settle_window_days": 10}
        )
        shop = self._pay(self.partners[0], 40.0)
        office = self._pay(self.partners[1], 40.0, self.day - timedelta(days=8), terminal_id=terminal)
        wizard = self._settlement(self._statement_line(40.0), terminal_id=terminal.id)
        self.assertEqual(wizard.line_ids.receipt_id, office)
        self.assertEqual(wizard.state, "proposed")
        self.assertNotIn(shop, wizard.line_ids.receipt_id)
        # Fără terminal, fereastra e cea mai largă dintre terminalele jurnalului.
        wizard = self._settlement(self._statement_line(80.0))
        self.assertEqual(wizard.line_ids.receipt_id, shop | office)

    def test_select_none(self):
        self._pay(self.partners[0], 60.0)
        wizard = self._settlement(self._statement_line(60.0))
        self.assertTrue(wizard.can_settle)
        action = wizard.action_select_none()
        self.assertEqual(action["res_id"], wizard.id)
        self.assertFalse(wizard.line_ids.filtered("selected"))
        self.assertFalse(wizard.can_settle)
        with self.assertRaisesRegex(UserError, "Tick the receipts"):
            wizard.action_settle()

    def test_search_limits(self):
        """Prea multe încasări sau o sumă prea mare: căutarea se oprește, bifarea e manuală."""
        Receipt = self.env["deltatech.expected.receipt"]
        currency = self.company.currency_id
        receipts = self._pay(self.partners[0], 10.0) | self._pay(self.partners[1], 20.0)
        many = Receipt.browse(receipts.ids * (MAX_CANDIDATES // 2 + 1))
        self.assertEqual(Receipt._find_exact_combinations(many, 30.0, currency), ([], "too_many"))
        too_big = MAX_TARGET_CENTS * currency.rounding + 1
        self.assertEqual(Receipt._find_exact_combinations(receipts, too_big, currency), ([], "too_complex"))
        self.assertEqual(Receipt._find_exact_combinations(receipts, 0.0, currency), ([], "target"))
        self.assertEqual(Receipt._find_exact_combinations(receipts, 5.0, currency), ([], "none"))
        self.assertEqual(Receipt._find_exact_combinations(receipts, 15.0, currency), ([], "none"))
        wizard = self._settlement(self._statement_line(30.0))
        for reason, text in (("too_many", "too many"), ("too_complex", "safety limit")):
            values = wizard._result_values(receipts, [], reason)
            self.assertEqual(values["state"], "manual")
            self.assertIn(text, values["message"])

    # ------------------------------------------------------------------
    #  Decontarea
    # ------------------------------------------------------------------
    def test_settle_refuses_a_receipt_no_longer_pending(self):
        receipt = self._pay(self.partners[0], 60.0)
        wizard = self._settlement(self._statement_line(60.0))
        receipt.with_user(self.manager).action_cancel()
        with self.assertRaisesRegex(UserError, "no longer pending"):
            wizard.action_settle()

    def test_settle_refuses_a_line_reconciled_meanwhile(self):
        receipt = self._pay(self.partners[0], 60.0)
        statement_line = self._statement_line(60.0)
        wizard = self._settlement(statement_line)
        self._reconcile_elsewhere(receipt, statement_line)
        with self.assertRaisesRegex(UserError, "no longer available"):
            wizard.action_settle()

    def test_settle_refuses_a_receipt_reconciled_meanwhile(self):
        """Plata a fost reconciliată cu altă linie între căutare și decontare."""
        receipt = self._pay(self.partners[0], 60.0)
        wizard = self._settlement(self._statement_line(60.0))
        self._reconcile_elsewhere(receipt, self._statement_line(60.0))
        with self.assertRaisesRegex(UserError, "reconciled meanwhile"):
            wizard.action_settle()

    def test_settle_posts_on_the_receipts(self):
        receipts = self._pay(self.partners[0], 25.0) | self._pay(self.partners[1], 35.0)
        statement_line = self._statement_line(60.0)
        action = self._settlement(statement_line).action_settle()
        self.assertEqual(self.env["deltatech.expected.receipt"].search(action["domain"]), receipts)
        for receipt in receipts:
            self.assertEqual(receipt.settlement_date, statement_line.date)
            self.assertIn("Settled by the bank statement", "".join(receipt.message_ids.mapped("body")))
