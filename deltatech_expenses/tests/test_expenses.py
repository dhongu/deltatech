# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import Form
from odoo.tests.common import TransactionCase


class TestExpenses(TransactionCase):
    def setUp(self):
        super(TestExpenses, self).setUp()
        self.employee = self.env["res.partner"].create({"name": "Test"})

        self.account_diem = self.env["account.account"].create(
            {
                "name": "Account Diem",
                "code": "625xxx",
                "user_type_id": self.env.ref("account.data_account_type_liquidity").id,
                "company_id": self.env.user.company_id.id,
            }
        )

    def test_create_expenses(self):
        form_expenses = Form(self.env["deltatech.expenses.deduction"])
        form_expenses.date_advance = fields.Date.today()
        form_expenses.advance = 1000
        form_expenses.employee_id = self.employee
        form_expenses.account_diem_id = self.account_diem

        expenses = form_expenses.save()
        expenses.validate_advance()

        form_expenses = Form(expenses)
        with form_expenses.expenses_line_ids.new() as line:
            line.name = "Test"
            line.amount = 300

        expenses = form_expenses.save()

        expenses.validate_expenses()
        expenses.invalidate_expenses()
