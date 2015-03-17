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
                if res['value']['price_unit'] < res['value']['purchase_price']:
                        warning = {
                               'title': _('Price Error!'),
                               'message' : _('You can not sell below the purchase price.'),
                            }
                        res['warning']  = warning
        return res
 
    def price_unit_change(self, cr, uid, ids, price_unit, purchase_price, context=None):
        res = {}
        if price_unit < purchase_price:
                warning = {
                       'title': _('Price Error!'),
                       'message' : _('You can not sell below the purchase price.'),
                    }
                res['warning']  = warning
        return res



    @api.one
    @api.constrains('price_unit', 'purchase_price')
    def _check_seats_limit(self):
        if not self.env.user.has_group('deltatech_sale_margin.group_sale_below_purchase_price'):
            if self.price_unit < self.purchase_price :
                raise Warning(_('You can not sell below the purchase price.'))

 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
