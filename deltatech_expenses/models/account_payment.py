from odoo import _, api, fields, models


class account_payment(models.Model):
    _inherit = "account.payment"

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction", string="Expenses Deduction", required=False)
