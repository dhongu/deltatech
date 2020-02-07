# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details




from odoo import fields, models, api


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    expenses_deduction_id = fields.Many2one('deltatech.expenses.deduction', string='Expenses Deduction', required=False)

    @api.multi
    def voucher_pay_now_payment_create(self):
        value = super(account_voucher, self).voucher_pay_now_payment_create()
        if 'expenses_deduction_id' in self.env.context:
            value['expenses_deduction_id'] = self.env.context['expenses_deduction_id']
        return value