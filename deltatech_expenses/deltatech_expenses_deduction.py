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
import openerp.addons.decimal_precision as dp

 

class deltatech_expenses_deduction(osv.osv):
    _name = 'deltatech.expenses.deduction'  
    _inherit = ['mail.thread']
    _description = 'Expenses Deduction'    


    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            total = 0.0
            for line in expense.line_ids:
                total += line.amount
            res[expense.id] = total
        return res

    def _difference(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            res[expense.id] = expense.amount - expense.advance  + expense.days * expense.diem 
        return res

    def _total_diem(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for expense in self.browse(cr, uid, ids, context=context):
            res[expense.id] = expense.days * expense.diem  
        return res

    def _get_currency(self, cr, uid, ids, name, args, context=None):
        res = {}
        for expense in self.browse(cr, uid, ids, context=context):
            res[expense.id] = expense.company_id.currency_id.id
        return res

    def _get_journal(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        res = journal_pool.search(cr, uid, [('type', '=', 'cash')], limit=1)
        return res and res[0] or False



    def _get_account_diem(self, cr, uid, context=None):
        account_pool = self.pool.get('account.account')
        try:
            account_id  = account_pool.search(cr, uid, [('code','ilike','625')], limit=1)[0]   ## Cheltuieli cu deplasari
        except (orm.except_orm, ValueError):
            try:
                account_id = account_pool.search(cr, uid, [('user_type.report_type','=','expense'), ('type','!=','view')], limit=1)[0]
            except (orm.except_orm, ValueError):
                account_id = False
        return   account_id 

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        return [(r['id'], (str("%.2f" % r['amount']) or '')) for r in self.read(cr, uid, ids, ['amount'], context, load='_classic_write')]

    _columns = {
        'number': fields.char('Number', size=32, readonly=True,),
        'state': fields.selection([
            ('draft','Draft'),
            ('done','Done'),
            ('cancel','Cancelled'),
            ],'Status', select=True, readonly=True, track_visibility='onchange',
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed expenses deduction. \
            \n* The \'Done\' status is set automatically when the expenses deduction is confirm.  \
            \n* The \'Cancelled\' status is used when user cancel expenses deduction.'),     
        'date_expense': fields.date('Expense Date', readonly=True, states={'draft':[('readonly',False)]}, select=True, help="Keep empty to use the current date"),
        
        'travel_order': fields.char(string='Travel Order', readonly=True, states={'draft':[('readonly',False)]}),
        
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'employee_id': fields.many2one('res.partner', "Employee", required=True, readonly=True, states={'draft':[('readonly',False)]}, domain=[('is_company','=',False)]),
#        'expenses_line_ids':fields.one2many('deltatech.expenses.deduction.line','expenses_deduction_id','Vouchers'),
         'line_ids':fields.one2many('account.voucher','expenses_deduction_id','Vouchers',
                                      domain=[('type','=','purchase')], context={'default_type':'purchase'}, readonly=True, states={'draft':[('readonly',False)]}),    
         'payment_ids':fields.one2many('account.voucher','expenses_deduction_id','Payments',
                                       domain=[('type','=','payment')], context={'default_type':'payment'}, readonly=True),  
        'note': fields.text('Note'),
        'amount': fields.function(_amount, string='Total Amount', digits_compute=dp.get_precision('Account')), 
        'advance': fields.float('Advance', digits_compute=dp.get_precision('Account'),  readonly=True, states={'draft':[('readonly',False)]}  ), 
        'difference': fields.function(_difference, string='Difference', digits_compute=dp.get_precision('Account')), 
        'currency_id': fields.function(_get_currency, type='many2one', relation='res.currency', string='Currency', readonly=True, required=True),   
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'account_id':fields.many2one('account.account','Account', required=True, readonly=True, states={'draft':[('readonly',False)]}), 
        'account_diem_id':fields.many2one('account.account','Account', required=True, readonly=True, states={'draft':[('readonly',False)]}), 
        'move_id':fields.many2one('account.move', 'Account Entry',readonly=True ),
        'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'diem': fields.float('Diem', digits_compute=dp.get_precision('Account'),  readonly=True, states={'draft':[('readonly',False)]}  ), 
        'days': fields.integer('Days', readonly=True, states={'draft':[('readonly',False)]}  ),  
        'total_diem':fields.function(_total_diem, string='Total Diem', digits_compute=dp.get_precision('Account')), 
    }

    _defaults = { 
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'date_expense': fields.date.context_today,
        'state': 'draft',
        'journal_id':_get_journal,
        'account_diem_id':_get_account_diem,
        #'employee_id': lambda cr, uid, id, c={}: id,
        'currency_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, context=c).company_id.currency_id.id,
        'diem': 32.5,
    }


    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}
        account_obj = self.pool.get('account.account')
        values = super(deltatech_expenses_deduction, self).default_get(cr, uid, fields_list, context=context)
        if 'account_id' in fields_list:
            try:
                account_id  = account_obj.search(cr, uid, [('code','ilike','542')])[0]
            except (orm.except_orm, ValueError):
                account_id = False
            values.update({'account_id': account_id})     
        return values   
 
    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete Expenses Deduction(s) which are already done.'))
        return super(deltatech_expenses_deduction, self).unlink(cr, uid, ids, context=context) 
 
    def validate_expenses(self, cr, uid, ids, context=None):
        voucher_pool = self.pool.get('account.voucher')
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        seq_pool = self.pool.get('ir.sequence')
        #poate ar fi bine cara  bonurile fiscale de la acelasi furnizor sa fie unuite intr-o singura chitanta.
        for expenses in self.browse(cr, uid, ids, context=context):
            voucher_ids = []
            for voucher in expenses.line_ids:
                if voucher.state == 'draft':
                    voucher_ids.append(voucher.id)
            voucher_pool.proforma_voucher(cr,uid,voucher_ids, context=context)
            for voucher in expenses.line_ids: 
                if not voucher.paid: 
                    partner_id = self.pool.get('res.partner')._find_accounting_partner(voucher.partner_id).id 
                    line_dr_ids = []
                    line_cr_ids = []
                    for line in voucher.move_ids: # de regula este o singura linie
                        if line.state == 'valid' and line.account_id.type == 'payable' and not line.reconcile_id:
                            amount_unreconciled = abs(line.amount_residual_currency)
                            rs = {
                                'name':line.move_id.name,
                                'type': line.credit and 'dr' or 'cr',
                                'move_line_id':line.id,
                                'account_id':line.account_id.id,
                                'amount_original': abs(line.amount_currency),
                                'amount': amount_unreconciled,
                                'date_original':line.date,
                                'date_due':line.date_maturity,
                                'amount_unreconciled': amount_unreconciled,
                                'currency_id': voucher.currency_id.id,
                                'reconcile':True
                            }
                            if rs['type'] == 'cr':
                                line_cr_ids.append([0,False,rs])
                            else:
                                line_dr_ids.append([0,False,rs])                          
                    
                    payment_id = voucher_pool.create(cr, uid, {
                                                           'journal_id':expenses.journal_id.id, 
                                                           'account_id':expenses.account_id.id, 
                                                           'type':'payment', 
                                                           'partner_id': voucher.partner_id.id, 
                                                           'reference':voucher.reference,
                                                           'amount':voucher.amount,
                                                           'line_dr_ids':line_dr_ids,
                                                           'line_cr_ids':line_cr_ids,
                                                           'expenses_deduction_id':expenses.id
                                                           }, 
                                                context = {'default_type':'payment',
                                                           'type':'payment',
                                                           'default_partner_id': partner_id ,
                                                           'default_partner_id': voucher.partner_id.id, 
                                                           'default_amount': voucher.amount,
                                                           'partner_id': partner_id, 
                                                           'default_reference':voucher.reference}) 
                    
                    voucher_pool.proforma_voucher(cr,uid,payment_id, context=context)
                    #nota catabila pentru plata!
                    """
                    move_line_dr = {
                            'name':  name or '/',
                            'debit': expenses.amount,
                            'credit': 0.0,
                            'account_id': expenses.account_id.id,
                            'journal_id': expenses.journal_id.id,
                            'date': expenses.date_expense,
                            'date_maturity': expenses.date_expense
                    }
                    move_line_cr = {
                        'name': name or '/',
                        'debit': 0.0,
                        'credit': expenses.amount,
                        'account_id': expenses.journal_id.default_credit_account_id.id,
                        'journal_id': expenses.journal_id.id,
                        'date': expenses.date_expense,
                        'date_maturity': expenses.date_expense
                    } 
                    """
                    
                    # TODO: de adaugat platile ca refeninta de decont
            name = seq_pool.next_by_id(cr, uid, expenses.journal_id.sequence_id.id, context=context)
            # Create the account move record.
            line_ids = []
            # nota contabila prin care banii au iesit din casa    
            move_line_dr = {
                'name':  name or '/',
                'debit': expenses.amount,
                'credit': 0.0,
                'account_id': expenses.account_id.id,
                'journal_id': expenses.journal_id.id,
                'date': expenses.date_expense,
                'date_maturity': expenses.date_expense
            }
            move_line_cr = {
                'name': name or '/',
                'debit': 0.0,
                'credit': expenses.amount,
                'account_id': expenses.journal_id.default_credit_account_id.id,
                'journal_id': expenses.journal_id.id,
                'date': expenses.date_expense,
                'date_maturity': expenses.date_expense
            }    
            line_ids.append([0,False,move_line_dr])   
            line_ids.append([0,False,move_line_cr])  
            if expenses.difference < 0:  
                move_line_cr = {
                    'name':  name or '/',
                    'debit': 0.0,
                    'credit':  abs(expenses.difference),
                    'account_id': expenses.account_id.id,
                    'journal_id': expenses.journal_id.id,
                    'date': expenses.date_expense,
                    'date_maturity': expenses.date_expense
                }
                move_line_dr = {
                    'name': name or '/',
                    'debit': abs(expenses.difference),
                    'credit': 0.0,
                    'account_id': expenses.journal_id.default_credit_account_id.id,
                    'journal_id': expenses.journal_id.id,
                    'date': expenses.date_expense,
                    'date_maturity': expenses.date_expense
                }                  
                line_ids.append([0,False,move_line_dr])   
                line_ids.append([0,False,move_line_cr]) 
            move_id = move_pool.create(cr, uid, {
                                        'name': name or '/',
                                        'journal_id': expenses.journal_id.id,
                                        'date': expenses.date_expense,
                                        'ref': name or '',
                                        'line_id':line_ids,
                                    }, context=context)
            name = move_pool.browse(cr, uid, move_id, context=context).name
            voucher_pool.write(cr,uid, [payment_id],{'state':'posted'})
            self.write(cr, uid, [expenses.id], {'state':'done','move_id':move_id,'number': name})
        return True  

    def cancel_expenses(self, cr, uid, ids,  context=None): 
        self.write(cr, uid, ids, {'state':'cancel'}, context) 
        return True  

    
deltatech_expenses_deduction()    
    
'''
class deltatech_expenses_deduction_line(osv.osv):
    _name = 'deltatech.expenses.deduction.line'  
    _description = 'Expenses Deduction Line'  
    
    def _amount(self, cr, uid, ids, field_name, arg, context=None):
        res= {}
        for line in self.browse(cr, uid, ids, context=context):
            total = line.unit_amount * line.unit_quantity
            res[line.id] = total
        return res
    
 
    
    _columns = {
        'name': fields.char('Expense Note', size=128),
        'date_expense': fields.date('Date', required=True),
        'expenses_deduction_id': fields.many2one('deltatech.expenses.deduction', 'Expense', ondelete='cascade', select=True),
        
        'amount': fields.function(_amount, string='Total', digits_compute=dp.get_precision('Account')),
        'unit_amount': fields.float('Unit Price', digits_compute=dp.get_precision('Product Price')),
        'unit_quantity': fields.float('Quantities', digits_compute= dp.get_precision('Product Unit of Measure')),
        'product_id': fields.many2one('product.product', 'Product'),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure'),
        'description': fields.text('Description'),
        'partner_id':fields.many2one('res.partner', 'Supplier'),
      
        'journal_id':fields.many2one('account.journal', 'Journal'),
        'account_id':fields.many2one('account.account', 'Account'),

        'reference': fields.char('Reference', size=32),
        'sequence': fields.integer('Sequence', select=True, help="Gives the sequence order when displaying a list of expense lines."),
    }   

    _defaults = {
        'unit_quantity': 1.0,     
    }


    def default_get(self, cr, uid, fields_list, context=None):
        if context is None:
            context = {}

        values = super(deltatech_expenses_deduction_line, self).default_get(cr, uid, fields_list, context=context)
        journal_id = context.get('journal_id', False)
        date_expense = context.get('date_expense', False)       
        account_obj = self.pool.get('account.account')
       
        try:
            account_id  = account_obj.search(cr, uid, [('code','ilike','623')])[0]   ## cheltuieli de protocol
        except (orm.except_orm, ValueError):
            account_id = False
    
        
        values.update({
            'journal_id':journal_id,
            'date_expense':date_expense,
            'account_id': account_id,
        })
        return values            
    
deltatech_expenses_deduction_line()  
'''
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: