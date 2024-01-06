# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestExpenses(TransactionCase):
    def setUp(self):
        super().setUp()

        # se creaza un angajat ca sa se poata crea o nota de cheltuieli
        self.employee = self.env["res.partner"].create({"name": "Test"})
        # se creaza un cont pentru diurna ca sa se poata crea o nota de cheltuieli
        self.account_diem = self.env["account.account"].create(
            {
                "name": "Account Diem",
                "code": "625xxx",
                "user_type_id": self.env.ref("account.data_account_type_liquidity").id,
                "company_id": self.env.user.company_id.id,
            }
        )
        # se creaza un cont pentru avans ca sa se poata crea o nota de cheltuieli
        self.account_cash_advances = self.env["account.account"].create(
            {
                "name": "account_cash_advances",
                "code": "542xxx",
                "user_type_id": self.env.ref("account.data_account_type_liquidity").id,
                "company_id": self.env.user.company_id.id,
            }
        )

    def test_create_expenses(self):
        # se creaza o nota de cheltuieli
        form_expenses = Form(self.env["deltatech.expenses.deduction"])
        form_expenses.date_advance = fields.Date.today()
        form_expenses.advance = 1000
        form_expenses.employee_id = self.employee
        form_expenses.account_diem_id = self.account_diem
        if not form_expenses.journal_id.account_cash_advances_id:
            form_expenses.journal_id.account_cash_advances_id = self.account_cash_advances

        # se salveaza nota de cheltuieli
        expenses = form_expenses.save()

        # se valideaza avansul
        expenses.validate_advance()

        # se verifica ca nota de cheltuieli este in starea avans
        self.assertEqual(expenses.state, "advance")

        # se adauga o linie de cheltuieli
        form_expenses = Form(expenses)
        with form_expenses.expenses_line_ids.new() as line:
            line.name = "Test"
            line.amount = 300

        # se salveaza nota de cheltuieli
        expenses = form_expenses.save()

        # se valideaza nota de cheltuieli
        expenses.validate_expenses()

        # se verifica ca nota de cheltuieli este in starea cheltuieli
        self.assertEqual(expenses.state, "done")

        # se verifica daca se poate face invalidarea cheltuielilor
        expenses.invalidate_expenses()

        # se verifica ca nota de cheltuieli este in starea draft
        self.assertEqual(expenses.state, "draft")
