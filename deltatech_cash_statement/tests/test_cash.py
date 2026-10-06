# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import date

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
