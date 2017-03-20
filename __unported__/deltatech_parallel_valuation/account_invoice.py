# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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

 

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_TIME_FORMAT
import time 
from datetime import datetime


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _get_default_currency_rate(self):
        res = None
        date_eval = self.env.context.get('date',False) or self.date_invoice or fields.Date.context_today(self) 
        to_currency = self.currency_id or self.env.user.company_id.currency_id
        from_currency = self.env.user.company_id.parallel_currency_id
        if to_currency and  from_currency:
            res = from_currency.with_context(date=date_eval).compute(1,to_currency,round=False)
        return res


    @api.multi
    def onchange_payment_term_date_invoice(self, payment_term_id, date_invoice):
        res = super(account_invoice,self).onchange_payment_term_date_invoice(payment_term_id, date_invoice)
        res['value']['currency_rate'] = self.with_context(date=date_invoice)._get_default_currency_rate() 
        return res
    
    currency_rate = fields.Float( string='Currency Rate', digits=(12, 4), readonly=True, states={'draft': [('readonly', False)]}, default=_get_default_currency_rate ) 
    
    date_invoice = fields.Date(string='Invoice Date',
        readonly=True, states={'draft': [('readonly', False)],
                               'proforma':[('readonly', False)],
                               'proforma2':[('readonly', False)]}, index=True,
        help="Keep empty to use the current date", copy=False)
    
    name = fields.Char(string='Reference/Description', index=True,
        readonly=True, states={'draft': [('readonly', False)],
                               'proforma':[('readonly', False)],
                               'proforma2':[('readonly', False)]})    
    

class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
 
    @api.one
    @api.depends('price_unit', 'purchase_price', 'quantity', 'discount', 'invoice_id.date_invoice' )
    def _compute_parallel_inventory_value(self):           
        if not self.invoice_id.currency_id:
            return
        date_eval = self.invoice_id.date_invoice or fields.Date.context_today(self) 
        from_currency = self.invoice_id.currency_id.with_context(date=date_eval)
        to_currency = self.env.user.company_id.parallel_currency_id
        if to_currency:
            line_value =  self.quantity * self.price_unit * (100.0-self.discount) / 100.0 
            if self.purchase_price:
                stock_value =  self.quantity * self.purchase_price
            else:
                stock_value = 0.0
            self.parallel_stock_value = from_currency.compute(stock_value, to_currency )
            self.parallel_line_value = from_currency.compute(line_value, to_currency )
    
    parallel_stock_value = fields.Float(string="Parallel Stock Value", digits= dp.get_precision('Product Price'),
                                             readonly=True, compute='_compute_parallel_inventory_value', store=True)  
     
    parallel_line_value = fields.Float(string="Parallel Line Value", digits= dp.get_precision('Product Price'),
                                             readonly=True, compute='_compute_parallel_inventory_value', store=True)    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
