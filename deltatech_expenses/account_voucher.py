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


from openerp.osv import fields, osv, orm 

#from openerp import models, fields, api, _
from openerp import models,  api, _
from openerp.exceptions import except_orm, ValidationError, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


class account_voucher(osv.osv):
    _inherit = 'account.voucher'  

    def _get_expense_account(self, cr, uid, context=None):
        account_pool = self.pool.get('account.account')
        try:
            account_id  = account_pool.search(cr, uid, [('code','ilike','623')], limit=1)[0]   ## cheltuieli de protocol
        except (orm.except_orm, ValueError):
            try:
                account_id = account_pool.search(cr, uid, [('user_type.report_type','=','expense'), ('type','!=','view')], limit=1)[0]
            except (orm.except_orm, ValueError):
                account_id = False
        return   account_id 

    def _expense_account(self, cr, uid, ids, name, args, context=None):
        res = {}

        account_id = self._get_expense_account(cr, uid, context )

                
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.type == 'purchase':
                if len(voucher.line_dr_ids)==1:
                    res[voucher.id] = voucher.line_dr_ids[0].account_id.id 
                else:
                    res[voucher.id] = account_id
            else:  
                res[voucher.id] = False      
        return res

    def _expense_account_inv(self, cr, uid, id, field_name, field_value, fnct_inv_arg, context):
        voucher = self.browse(cr, uid, id, context=context)
        if voucher.type == 'purchase' and len(voucher.line_dr_ids)==1:
            self.write(cr, uid, [id], {'line_dr_ids':[[1,voucher.line_dr_ids[0].id,{'account_id':field_value}]]}, context)
        return True

    def _get_partner_id(self, cr, uid, context=None):
        try:
            model, partner_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'deltatech_expenses', 'partner_generic')
        except (orm.except_orm, ValueError):
            partner_id = False
        return partner_id

    _columns = {
        'expenses_deduction_id': fields.many2one('deltatech.expenses.deduction', 'Expenses Deduction', required=False),  
        'default_expense_account_id':fields.function(_expense_account, fnct_inv=_expense_account_inv,  type='many2one', relation='account.account', string='Default Expense Account'),             
    }

    _defaults = {
        'partner_id': _get_partner_id,
        'default_expense_account_id':_get_expense_account,
    }
 
    @api.model
    def create(self,    vals  ):   
        if not vals.get('line_dr_ids', False):
            if vals.get('type') == 'purchase':              
                account_id = vals.get('default_expense_account_id',False)
                line_vals = {'account_id': account_id, 'amount':vals.get('amount', 0)}
                if 'tax_id' in vals:
                    tax = self.env['account.tax'].browse(vals['tax_id'])
                    if tax:
                        taxes = tax.compute_inv( taxes = tax, price_unit=vals.get('amount', 0), quantity = 1)
                        
                        line_vals['untax_amount'] = taxes[0]['price_unit']
                        vals['tax_amount'] = taxes[0]['amount']
                     
                print   vals, line_vals 
                vals['line_dr_ids'] = [[0,False,line_vals]]
                    
        res =  super(account_voucher, self).create(   vals ) 
        return res

    @api.multi
    def write(self,    vals ):
        res = super(account_voucher, self).write(  vals )
        if 'amount' in vals:
            for voucher in self:
                if voucher.type == 'purchase':
                    if len(voucher.line_dr_ids)==1:
                        voucher.line_dr_ids.write({'amount':voucher.amount})
        """             
        if 'tax_id' in vals:
            for voucher in self:
                if voucher.type == 'purchase':
                    if len(voucher.line_dr_ids)==1:
                        tax = self.env['account.tax'].browse(vals['tax_id'])
                        
                        taxes = tax.compute_all( voucher.line_dr_ids.amount, 1, force_excluded=True)
                        print taxes
                        voucher.line_dr_ids.write({'amount':taxes['total_included'], 'untax_amount':taxes['total']})
        """                
        return res

 
    
    def confirm_voucher(self, cr, uid, ids, context=None):
        
        active_ids = context.get('active_ids',ids)
        ids = []
        for voucher in self.browse(cr, uid, active_ids, context=context):
            if voucher.state == 'draft':
                ids.append(voucher.id)
        if len(ids) > 0:
            self.action_move_line_create(cr, uid, ids, context=context)
        return True
    
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
        res = super(account_voucher,self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context)
        if journal_id and not res['value']['account_id']: 
            journal_pool = self.pool.get('account.journal')
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id or False
            res['value']['account_id'] = account_id
        return res
                   
         
 
account_voucher()    
    




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: