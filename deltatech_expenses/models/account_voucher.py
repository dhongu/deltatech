# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class account_voucher(models.Model):
    _inherit = "account.voucher"

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction", string="Expenses Deduction", required=False)
