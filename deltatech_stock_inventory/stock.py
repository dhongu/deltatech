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
from openerp.tools import float_compare, float_is_zero
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api

import openerp.addons.decimal_precision as dp


class stock_inventory(models.Model):
    _inherit = 'stock.inventory'

    date = fields.Datetime(string='Inventory Date', required=True, readonly=True, states={'draft': [('readonly', False)]})



    @api.multi    
    def prepare_inventory(self):
        res = super(stock_inventory, self).prepare_inventory()
        for inventory in self:
            date = inventory.date
            inventory.write({ 'date': date})
            for line in  inventory.line_ids:
                line.write({'standard_price':line.get_price()})
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

    @api.one
    @api.onchange('theoretical_qty')
    def onchange_theoretical_qty(self):
        self.standard_price = self.get_price()


    @api.model
    def get_price(self):                
        price  =  self.product_id.standard_price 
        if  self.product_id.cost_method == 'real': 
            dom = [('company_id', '=', self.company_id.id), ('location_id', '=', self.location_id.id), ('lot_id', '=', self.prod_lot_id.id),
                        ('product_id','=', self.product_id.id), ('owner_id', '=', self.partner_id.id), ('package_id', '=', self.package_id.id)]
            dom = [('location_id', '=', self.location_id.id),     ('product_id','=', self.product_id.id) , ('lot_id', '=', self.prod_lot_id.id), 
                   ('owner_id', '=', self.partner_id.id), ('package_id', '=', self.package_id.id)]
             
            quants = self.env['stock.quant'].search(dom)
            
            value = sum([q.inventory_value for q in quants])
            if self.theoretical_qty > 0:
                price = value / self.theoretical_qty
             
        return price
    
    """
    def onchange_createline(self, cr, uid, ids, location_id=False, product_id=False, uom_id=False, package_id=False,
                                                prod_lot_id=False, partner_id=False, company_id=False, context=None):
        res = super(stock_inventory_line,self).onchange_createline( cr, uid, ids, location_id, product_id, uom_id, package_id,
                                                                        prod_lot_id, partner_id, company_id, context)
        if product_id:
            res['value']['standard_price'] = self.get_price(cr, uid, product_id, location_id )
        return res
    """

    @api.model
    def _resolve_inventory_line(self,  inventory_line):  
        if inventory_line.product_id.cost_method == 'real':
            price = inventory_line.get_price( )           
            product_qty = inventory_line.product_qty
            
           
            if not float_is_zero(abs(inventory_line.standard_price - price), precision_digits=2 ): 
                
                line_price = inventory_line.standard_price
                inventory_line.write( {'standard_price': price, 'product_qty':0.0 } )
                inventory_line.product_id.write({'standard_price':price} )
                move_id = super(stock_inventory_line,self)._resolve_inventory_line(    inventory_line )
                if move_id:
                    move = self.env['stock.move'].browse(move_id)
                    move.action_done()
                inventory_line.write( {'standard_price': line_price, 'product_qty':product_qty + inventory_line.theoretical_qty } )
                
            inventory_line.product_id.write( {'standard_price':inventory_line.standard_price}  ) 
            move_id = super(stock_inventory_line,self)._resolve_inventory_line(    inventory_line )
            if   product_qty <> inventory_line.product_qty:
                inventory_line.write( {'product_qty':product_qty } )
            if move_id:
                move = self.env['stock.move'].browse(move_id)
                move.action_done()
        return move_id
 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
