from odoo import fields, models


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction")
