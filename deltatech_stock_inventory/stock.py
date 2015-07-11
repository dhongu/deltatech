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

from datetime import date, datetime
from dateutil import relativedelta

import time
from openerp.exceptions import except_orm, Warning, RedirectWarning
 
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api

import openerp.addons.decimal_precision as dp


class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    date = fields.Datetime(string='Inventory Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
   
    def prepare_inventory(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            date = inventory.date
            res = super(stock_inventory, self).prepare_inventory(cr, uid, [inventory.id], context)
            self.write(cr, uid, inventory.id, { 'date': date})
        return res    
    
    def action_done(self, cr, uid, ids, context=None):
        super(stock_inventory,self).action_done(cr, uid, ids, context)
        for inv in self.browse(cr, uid, ids, context=context):
            for move in inv.move_ids:
                if move.date_expected != inv.date or move.date != inv.date   :
                    self.pool.get('stock.move').write(cr, uid, [move.id], { 'date_expected': inv.date, 'date':inv.date }, context )
        return True
 
class stock_inventory_line(models.Model):
    _inherit = "stock.inventory.line"

    standard_price = fields.Float(string='Price')

    
    def onchange_createline(self, cr, uid, ids, location_id=False, product_id=False, uom_id=False, package_id=False,
                                                prod_lot_id=False, partner_id=False, company_id=False, context=None):
        res = super(stock_inventory_line,self).onchange_createline( cr, uid, ids, location_id, product_id, uom_id, package_id,
                                                                        prod_lot_id, partner_id, company_id, context)
        if product_id:
            obj_product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            return {'value': {'standard_price':  obj_product.standard_price}}        
        return res


    def _resolve_inventory_line(self, cr, uid, inventory_line, context=None):  
        if inventory_line.product_id.cost_method == 'real':
            self.pool.get('product.product').write(cr, uid, inventory_line.product_id.id,{'standard_price':inventory_line.standard_price},context )
            move_id = super(stock_inventory_line,self)._resolve_inventory_line(  cr, uid, inventory_line, context)
            move_obj = self.pool.get('stock.move')
            move_obj.action_done(cr, uid, move_id, context=context)
        return move_id
 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
