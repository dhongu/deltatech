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
 

    purchase_price = fields.Float(string='Cost Price', digits= dp.get_precision('Product Price'))
    commission =  fields.Float(string="Commission",default=0.0) 
    

    def price_unit_change(self, cr, uid, ids, price_unit, purchase_price, context=None):
        res = {}
        if price_unit < purchase_price and purchase_price > 0:
                warning = {
                       'title': _('Price Error!'),
                       'message' : _('You can not sell below the purchase price.'),
                    }
                res['warning']  = warning
        return res

    @api.one
    @api.constrains('price_unit', 'purchase_price')
    def _check_seats_limit(self):
        if not self.env['res.users'].has_group('deltatech_sale_margin.group_sale_below_purchase_price'):
            date_eval = self.invoice_id.date_invoice or fields.Date.context_today(self)
            if  self.invoice_id.currency_id and self.invoice_id.currency_id.id <> self.env.user.company_id.currency_id.id:
                from_currency = self.invoice_id.currency_id.with_context(date=date_eval)
                price_unit = from_currency.compute(self.price_unit, self.env.user.company_id.currency_id )
            else:
                price_unit = self.price_unit
            if price_unit < self.purchase_price and purchase_price > 0 :
                raise Warning(_('You can not sell below the purchase price.'))


    @api.model
    def create(self,   values ):
        if values.get('product_id') and values.get('invoice_id') and 'price_unit' not in values :
            
            invoice = self.env['account.invoice'].browse(values['invoice_id'])
       
            defaults = self.product_id_change(values['product_id'],
                                              uom_id = values.get('uos_id', False),
                                              qty=float(values.get('quantity', False)),
                                              name=values.get('name', False),
                                              type=invoice.type,
                                              partner_id=invoice.partner_id.id,
                                              fposition_id=invoice.fiscal_position.id if invoice.fiscal_position else False,
                                              price_unit=False,
                                              currency_id=invoice.currency_id.id if invoice.currency_id else False,
                                              company_id=invoice.company_id.id)
            values['price_unit'] = defaults['value']['price_unit']
        return super(account_invoice_line, self).create(  values )
    
    @api.multi
    def write(self, values):  
        if values.get('product_id')  and 'price_unit' not in values :
            invoice = self[0].invoice_id     
            defaults = self.product_id_change(values['product_id'],
                                              uom_id = values.get('uos_id', self[0].uos_id.id if self[0].uos_id else False),
                                              qty=float(values.get('quantity', self[0].quantity)),
                                              name=values.get('name', self[0].name),
                                              type=invoice.type,
                                              partner_id=invoice.partner_id.id,
                                              fposition_id=invoice.fiscal_position.id if invoice.fiscal_position else False,
                                              price_unit=False,
                                              currency_id=invoice.currency_id.id if invoice.currency_id else False,
                                              company_id=invoice.company_id.id)
            values['price_unit'] = defaults['value']['price_unit']            
        return super(account_invoice_line, self).write(values)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
