# -*- coding: utf-8 -*-





from odoo import fields, models, api


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    expenses_deduction_id = fields.Many2one('deltatech.expenses.deduction', string='Expenses Deduction', required=False)

