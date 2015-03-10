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

 

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_TIME_FORMAT
import time 
from datetime import datetime



class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"
 
    @api.one
    @api.depends('price_unit', 'purchase_price', 'quantity', 'discount', 'invoice_id.date_invoice' )
    def _compute_parallel_inventory_value(self):           
        date_eval = self.invoice_id.date_invoice or fields.Date.context_today(self) 
        from_currency = self.invoice_id.currency_id.with_context(date=date_eval)
        to_currency = self.env.user.company_id.parallel_currency_id
        if to_currency:
           line_value =  self.quantity * self.price_unit * (100.0-self.discount) / 100.0 
           stock_value =  self.quantity * self.purchase_price             
           self.parallel_stock_value = from_currency.compute(stock_value, to_currency )
           self.parallel_line_value = from_currency.compute(line_value, to_currency )
    
    parallel_stock_value = fields.Float(string="Parallel Stock Value", digits= dp.get_precision('Product Price'),
                                             readonly=True, compute='_compute_parallel_inventory_value', store=True)  
     
    parallel_line_value = fields.Float(string="Parallel Line Value", digits= dp.get_precision('Product Price'),
                                             readonly=True, compute='_compute_parallel_inventory_value', store=True)    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
