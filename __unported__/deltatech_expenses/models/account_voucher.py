# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
##############################################################################




from odoo import fields, models, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class account_voucher(models.Model):
    _inherit = 'account.voucher'


    @api.model
    def _default_expense_account(self):
        account_pool = self.env['account.account']
        account = account_pool.search([('code', 'ilike', '623')], limit=1)  ## cheltuieli de protocol
        if not account:
            account = account_pool.search([('user_type.report_type', '=', 'expense'),
                                               ('type', '!=', 'view')],  limit=1)
        return account

    @api.multi
    def _default_expense_account(self):
        res = {}

        account = self._default_expense_account()

        for voucher in self.browse:
            if voucher.voucher_type == 'purchase':
                if len(voucher.line_dr_ids) == 1:
                    res[voucher.id] = voucher.line_dr_ids[0].account_id.id
                else:
                    res[voucher.id] = account_id
            else:
                res[voucher.id] = False
        return res

    def _expense_account_inv(self, cr, uid, id, field_name, field_value, fnct_inv_arg, context):
        voucher = self.browse(cr, uid, id, context=context)
        if voucher.voucher_type == 'purchase' and len(voucher.line_dr_ids) == 1:
            self.write(cr, uid, [id], {'line_dr_ids': [[1, voucher.line_dr_ids[0].id, {'account_id': field_value}]]},
                       context)
        return True

    @api.model
    def _get_partner_id(self):
        try:
            partner_id = self.env.ref('deltatech_expenses.partner_generic')
        except:
            partner_id = False
        return partner_id

    partner_id = fields.Many2one('res.partner', defualt=lambda self: self._get_partner_id)
    expenses_deduction_id = fields.Many2one('deltatech.expenses.deduction', string='Expenses Deduction', required=False)
    expense_account_id = fields.Many2one('account.account',
                                                 compute="_comute_expense_account",
                                                 string='Default Expense Account')

    @api.multi
    def _comute_expense_account(self):
        account_id =  self._default_expense_account()
        for voucher in self:
            if voucher.voucher_type == 'purchase':
                if len(voucher.line_dr_ids) == 1:
                    voucher.expense_account_id = voucher.line_dr_ids[0].account_id
                else:
                    voucher.expense_account_id = account_id

    @api.model
    def create(self, vals):
        if not vals.get('line_dr_ids', False):
            if vals.get('voucher_type') == 'purchase':
                account_id = vals.get('default_expense_account_id', False)
                line_vals = {'account_id': account_id, 'amount': vals.get('amount', 0)}
                if 'tax_id' in vals:
                    tax = self.env['account.tax'].browse(vals['tax_id'])
                    if tax:
                        taxes = tax.compute_inv(taxes=tax, price_unit=vals.get('amount', 0), quantity=1)

                        line_vals['untax_amount'] = taxes[0]['price_unit']
                        vals['tax_amount'] = taxes[0]['amount']

                print   vals, line_vals
                vals['line_dr_ids'] = [[0, False, line_vals]]

        res = super(account_voucher, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(account_voucher, self).write(vals)
        if 'amount' in vals:
            for voucher in self:
                if voucher.voucher_type == 'purchase':
                    if len(voucher.line_dr_ids) == 1:
                        voucher.line_dr_ids.write({'amount': voucher.amount})

        return res

    @api.multi
    def confirm_voucher(self):

        active_ids = context.get('active_ids', ids)
        ids = []
        for voucher in self.browse(cr, uid, active_ids, context=context):
            if voucher.state == 'draft':
                ids.append(voucher.id)
        if len(ids) > 0:
            self.action_move_line_create(cr, uid, ids, context=context)
        return True

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        res = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount,
                                                               currency_id, ttype, date, context)
        if journal_id and not res['value']['account_id']:
            journal_pool = self.pool.get('account.journal')
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id or False
            res['value']['account_id'] = account_id
        return res









        # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
