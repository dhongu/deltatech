# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields
from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestExpenses(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        ro_template_ref = "l10n_ro.ro_chart_template"
        super().setUpClass(chart_template_ref=ro_template_ref)
        if "l10n_ro_accounting" in cls.env.user.company_id._fields:
            cls.env.company.l10n_ro_accounting = True

        cls.employee = cls.env["res.partner"].create({"name": "Test"})

        cls.account_diem = cls.env["account.account"].create(
            {
                "name": "Account Diem",
                "code": "625xxx",
                "account_type": "expense",
                "company_id": cls.env.user.company_id.id,
            }
        )

        cls.account_cash_advances = cls.env["account.account"].create(
            {
                "name": "account_cash_advances",
                "code": "542xxx",
                "account_type": "asset_cash",
                "company_id": cls.env.user.company_id.id,
            }
        )

    def test_create_expenses(self):
        form_expenses = Form(self.env["deltatech.expenses.deduction"])
        form_expenses.date_advance = fields.Date.today()
        form_expenses.advance = 1000
        form_expenses.employee_id = self.employee
        form_expenses.account_diem_id = self.account_diem
        if not form_expenses.journal_id.account_cash_advances_id:
            form_expenses.journal_id.account_cash_advances_id = self.account_cash_advances

        expenses = form_expenses.save()
        expenses.validate_advance()

        form_expenses = Form(expenses)
        with form_expenses.expenses_line_ids.new() as line:
            line.name = "Test"
            line.amount = 300

        expenses = form_expenses.save()

        expenses.validate_expenses()
        expenses.invalidate_expenses()
