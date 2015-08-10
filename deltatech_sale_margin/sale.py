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



 
class sale_order_line(models.Model):
    _inherit = "sale.order.line"



    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False, fiscal_position=False, flag=False, context=None):
        
        res = super(sale_order_line, self).product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order, packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)
        
        if not res['value'].get('warning', False):
            if 'price_unit' in res['value'] and 'purchase_price' in res['value']:
                if res['value']['price_unit'] < res['value']['purchase_price'] and res['value']['purchase_price'] > 0:
                        warning = {
                               'title': _('Price Error!'),
                               'message' : _('You can not sell below the purchase price.'),
                            }
                        res['warning']  = warning
        return res
 
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
            if self.price_unit < self.purchase_price :
                raise Warning(_('You can not sell below the purchase price.'))

    @api.multi
    def write(self, values):  
        if values.get('product_id')  and 'price_unit' not in values :
            order = self[0].order_id     

            defaults = self.product_id_change(  pricelist = order.pricelist_id.id, 
                                                product =  values['product_id'],
                                                qty = float(values.get('product_uom_qty', self[0].product_uom_qty)),
                                                uom = values.get('product_uom', self[0].product_uom.id if self[0].product_uom else False),
                                                qty_uos = float(values.get('product_uos_qty', self[0].product_uos_qty)), 
                                                uos=values.get('product_uos', self[0].product_uos.id if self[0].product_uos else False),
                                                name=values.get('name', False),
                                                partner_id=order.partner_id.id,                                               
                                                date_order=order.date_order,
                                                fiscal_position=order.fiscal_position.id if order.fiscal_position else False,
                                            )                                
                                                                                        
            values['price_unit'] = defaults['value']['price_unit']            
        return super(sale_order_line, self).write(values) 
 
 

 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
