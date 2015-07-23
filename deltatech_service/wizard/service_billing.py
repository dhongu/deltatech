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
##############################################################################



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class service_billing(models.TransientModel):
    _name = 'service.billing'
    _description = "Service Billing"
    
    journal_id = fields.Many2one('account.journal', 'Journal', required=True)
    date_invoice = fields.Date(string='Invoice Date', required=True)
    group_service = fields.Boolean(string="Group by service")
    consumption_ids = fields.Many2many('service.consumption', 'service_billing_consumption', 'billing_id','consumption_id', 
                                        string='Consumptions', domain=[('invoice_id', '=', False)])
        
    @api.model
    def default_get(self, fields):
        defaults = super(service_billing, self).default_get(fields)
      
        
        active_ids = self.env.context.get('active_ids', False)
        print active_ids
        if active_ids:
            domain=[('invoice_id', '=', False),('id','in', active_ids )]   
        else:
            domain=[('invoice_id', '=', False)]
        
        
        res = self.env['service.consumption'].search(domain)
        defaults['consumption_ids'] = [ (6,0,[rec.id for rec in res]) ]
        return defaults
        

    @api.multi
    def do_billing(self):
        pre_invoice = {}
        for cons in self.consumption_ids:
            # convertire pret in moneda companeie
            
            currency = cons.currency_id.with_context(date=self.date_invoice or fields.Date.context_today(self)) 
             
            price_unit = currency.compute(cons.price_unit, self.env.user.company_id.currency_id )
            
            name =  cons.product_id.name

            if cons.name and not self.group_service:
                name = name + ' ' + cons.name
                
            if cons.quantity > cons.agreement_line_id.quantity_free:
                invoice_line = {
                    'product_id': cons.product_id.id,
                    'quantity': cons.quantity - cons.agreement_line_id.quantity_free,
                    'price_unit': price_unit ,
                    'name': name,
                    'account_id': cons.product_id.property_account_income.id or cons.product_id.categ_id.property_account_income_categ.id,
                    'invoice_line_tax_id'  : [(6, 0, (  [rec.id for rec in cons.product_id.taxes_id] ))]
                }
    
                if pre_invoice.get(cons.agreement_id.id,False):
                    is_prod = False
                    if self.group_service:
                        for line in pre_invoice[cons.agreement_id.id]['lines']:
                            if line['product_id'] ==  cons.product_id.id and  float_compare(line['price_unit'],invoice_line['price_unit']) == 0 :
                                line['quantity'] += invoice_line['quantity']
                                is_prod = True
                                break
                    if not is_prod:   
                        pre_invoice[cons.agreement_id.id]['lines'].append(invoice_line)
                    pre_invoice[cons.agreement_id.id]['cons'] += cons
                else:
                    comment = _('According to agreement %s from %s') % (cons.agreement_id.name or '____', cons.agreement_id.date_agreement or '____')
                    pre_invoice[cons.agreement_id.id] = {'lines':[invoice_line],
                                                       'cons':cons,
                                                       'comment':  comment,
                                                       'agreement_id':cons.agreement_id.id,
                                                       'partner_id':cons.partner_id.id,
                                                       'account_id':cons.partner_id.property_account_receivable.id, }
        
            
        res = []
        for key in pre_invoice:
            
            invoice_value = { 
                #'name': _('Invoice'),
                'partner_id': pre_invoice[key]['partner_id'],
                'journal_id': self.journal_id.id,
                'date_invoice':self.date_invoice,
                'account_id': pre_invoice[key]['account_id'], 
                'type': 'out_invoice',
                'state': 'draft',
                'invoice_line': [(0, 0, x) for x in pre_invoice[key]['lines']],
                'comment':pre_invoice[key]['comment'],
                'agreement_id':pre_invoice[key]['agreement_id'],
            }
            invoice_id = self.env['account.invoice'].create(invoice_value)
            invoice_id.button_compute(True)
            pre_invoice[key]['cons'].write( {'invoice_id':invoice_id.id,'state':'done'})
            res.append(invoice_id.id)
        return {
            'domain': "[('id','in', ["+','.join(map(str,res))+"])]",
            'name': _('Services Invoices'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'context': "{'type':'out_invoice', 'journal_type': 'sale'}",
            'type': 'ir.actions.act_window'
        }
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 