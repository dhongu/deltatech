# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestCash(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("ro")
    def setUpClass(cls):
        super().setUpClass()
        cls.journal = cls.company_data["default_journal_cash"]
        cls.cash_account = cls.journal.default_account_id
        cls.income = cls.env["account.account"].create(
            {"name": "Other income", "code": "758899", "account_type": "income_other"}
        )
        cls.previous = cls._statement(date(2026, 3, 1), 500.0)
        cls.statement = cls._statement(date(2026, 3, 2), 50.0)

    @classmethod
    def _statement(cls, day, amount):
        line = cls.env["account.bank.statement.line"].create(
            {
                "journal_id": cls.journal.id,
                "date": day,
                "payment_ref": f"Cash {day}",
                "amount": amount,
                "counterpart_account_id": cls.income.id,
            }
        )
        statement = cls.env["account.bank.statement"].create({"name": f"CSH {day}", "line_ids": [(6, 0, line.ids)]})
        return statement

    def _wizard(self, statements, **values):
        form = Form(self.env["account.cash.update.balances"].with_context(active_ids=statements.ids))
        for name, value in values.items():
            setattr(form, name, value)
        return form.save()

    def test_align_with_accounting_balance(self):
        """The starting balance follows the cash account; no entry is created."""
        self.statement.write({"balance_start": 0.0, "balance_end_real": 50.0})
        moves_before = self.env["account.move"].search_count([("journal_id", "=", self.journal.id)])
        wizard = self._wizard(self.statement)
        self.assertEqual(wizard.accounting_balance, 500.0)
        wizard.do_update_balance()
        self.assertEqual(self.statement.balance_start, 500.0)
        self.assertEqual(self.statement.balance_end_real, 550.0)
        self.assertEqual(self.env["account.move"].search_count([("journal_id", "=", self.journal.id)]), moves_before)

    def test_cash_shortage_is_booked_on_6588(self):
        """Counted 480 instead of 500: 6588 = 5311 for 20, dated, in the statement."""
        wizard = self._wizard(self.statement, mode="difference", counted_balance=480.0)
        self.assertEqual(wizard.difference, -20.0)
        expense = wizard.counterpart_account_id
        self.assertTrue(expense.code.startswith("6588"))
        wizard.do_update_balance()
        line = self.statement.line_ids.filtered(lambda st_line: st_line.amount == -20.0)
        self.assertEqual(line.date, date(2026, 3, 2))
        self.assertRecordValues(
            line.move_id.line_ids.sorted("balance"),
            [
                {"account_id": self.cash_account.id, "balance": -20.0},
                {"account_id": expense.id, "balance": 20.0},
            ],
        )
        self.assertEqual(self.statement.balance_start, 500.0)
        self.assertEqual(self.statement.balance_end_real, 530.0)

    def test_cash_surplus_is_booked_on_7588(self):
        wizard = self._wizard(self.statement, mode="difference", counted_balance=510.0)
        self.assertTrue(wizard.counterpart_account_id.code.startswith("7588"))
        wizard.do_update_balance()
        self.assertEqual(self.statement.balance_end_real, 560.0)

    def test_chain_of_statements(self):
        """Each following statement starts from the real ending balance of the previous one."""
        statements = self.previous | self.statement
        statements.write({"balance_start": 0.0})
        self._wizard(statements).do_update_balance()
        self.assertEqual(self.previous.balance_start, 0.0)
        self.assertEqual(self.previous.balance_end_real, 500.0)
        self.assertEqual(self.statement.balance_start, 500.0)
        self.assertEqual(self.statement.balance_end_real, 550.0)

    def test_shortage_charged_to_cashier_needs_partner(self):
        """4282: the receivable is followed on the person responsible."""
        account_4282 = self.env["account.account"].search(
            [("code", "=like", "4282%"), ("company_ids", "in", self.env.company.ids)], limit=1
        )
        cashier = self.env["res.partner"].create({"name": "Casier"})
        wizard = self._wizard(self.statement, mode="difference", counted_balance=490.0)
        wizard.counterpart_account_id = account_4282
        self.assertTrue(wizard.partner_required)
        with self.assertRaises(UserError):
            wizard.do_update_balance()
        wizard.partner_id = cashier
        wizard.do_update_balance()
        line = self.statement.line_ids.filtered(lambda st_line: st_line.amount == -10.0)
        receivable = line.move_id.line_ids.filtered(lambda aml: aml.account_id == account_4282)
        self.assertEqual(receivable.partner_id, cashier)

    def test_difference_not_dated_before_statement(self):
        wizard = self._wizard(self.statement, mode="difference", counted_balance=490.0)
        wizard.date = date(2026, 3, 1)
        with self.assertRaises(UserError):
            wizard.do_update_balance()

    def _second_journal_statements(self):
        """Second cash journal with statements interleaved by date with the first journal."""
        journal_b = self.env["account.journal"].create({"name": "Cash B", "type": "cash", "code": "CSHB"})
        statements_b = self.env["account.bank.statement"]
        for day, amount in ((date(2026, 3, 1), 200.0), (date(2026, 3, 3), 30.0)):
            line = self.env["account.bank.statement.line"].create(
                {
                    "journal_id": journal_b.id,
                    "date": day,
                    "payment_ref": f"Cash B {day}",
                    "amount": amount,
                    "counterpart_account_id": self.income.id,
                }
            )
            statements_b |= self.env["account.bank.statement"].create(
                {"name": f"CSHB {day}", "line_ids": [(6, 0, line.ids)]}
            )
        return statements_b

    def test_batch_on_two_journals_chains_each_journal(self):
        """Statements of two cash journals, interleaved by date: each journal keeps its own chain."""
        statements_a = self.previous | self.statement
        statements_b = self._second_journal_statements()
        (statements_a | statements_b).write({"balance_start": 999.0})
        wizard = self._wizard(statements_a | statements_b)
        self.assertTrue(wizard.multi_journal)
        wizard.do_update_balance()
        self.assertRecordValues(
            statements_a | statements_b,
            [
                {"balance_start": 0.0, "balance_end_real": 500.0},
                {"balance_start": 500.0, "balance_end_real": 550.0},
                {"balance_start": 0.0, "balance_end_real": 200.0},
                {"balance_start": 200.0, "balance_end_real": 230.0},
            ],
        )

    def test_other_journal_in_context_is_not_chained(self):
        """The wizard only touches its own statements, whatever active_ids the button sends."""
        statements_b = self._second_journal_statements()
        statements_b.write({"balance_start": 999.0})
        wizard = self._wizard(self.previous | self.statement)
        wizard.with_context(active_ids=(self.previous | self.statement | statements_b).ids).do_update_balance()
        self.assertEqual(statements_b.mapped("balance_start"), [999.0, 999.0])
        self.assertEqual(self.statement.balance_start, 500.0)

    def test_cash_difference_needs_a_single_journal(self):
        wizard = self._wizard(self.statement | self._second_journal_statements())
        wizard.mode = "difference"
        with self.assertRaises(UserError):
            wizard.do_update_balance()
