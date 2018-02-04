# -*- coding: utf-8 -*-


from odoo import fields, models, api, _


class account_payment(models.Model):
    _inherit = "account.payment"


    expenses_deduction_id = fields.Many2one('deltatech.expenses.deduction', string='Expenses Deduction', required=False)