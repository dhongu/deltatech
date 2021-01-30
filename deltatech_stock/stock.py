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
import json
import time

from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api

import openerp.addons.decimal_precision as dp


class stock_pack_operation(osv.osv):
    _inherit = "stock.pack.operation"

    def create(self, cr, uid, vals, context=None):
        context = context or {}
        if vals.get("picking_id"):
            picking = self.pool.get("stock.picking").browse(cr, uid, vals['picking_id'], context=context)
            vals['date'] = picking.min_date  # trebuie sa fie minimul dintre data curenta si data din picking
        res_id = super(stock_pack_operation, self).create(cr, uid, vals, context=context)
        return res_id


class stock_quant(osv.osv):
    _inherit = "stock.quant"
    
    def _quant_create(self, cr, uid, qty, move, lot_id=False, owner_id=False, src_package_id=False, dest_package_id=False, force_location_from=False, force_location_to=False, context=None):
        quant = super(stock_quant, self)._quant_create(cr, uid, qty, move, lot_id=lot_id, owner_id=owner_id, src_package_id=src_package_id, dest_package_id=dest_package_id, force_location_from=force_location_from, force_location_to=force_location_to, context=context)
        #quant.in_date = move.date
        self.write(cr, uid, [quant.id], {'in_date': move.date_expected }, context=context)
        return quant    
    
          
                   
    
class stock_move(osv.osv):
    _inherit = 'stock.move'

    def write(self, cr, uid, ids, vals, context=None):   
        date_fields = set(['date', 'date_expected'])
        if date_fields.intersection(vals):
            for move in self.browse(cr, uid, ids, context=context):
                today = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
                if 'date' in vals:
                    if move.date_expected[:10] < today and move.date_expected < vals['date']:
                        vals['date'] =  move.date_expected
                    if move.date[:10] < today and move.date < vals['date']:
                        vals['date'] =  move.date                      
                if 'date_expected' in vals:
                    if move.date[:10] < today and move.date < vals['date_expected']:
                        vals['date_expected'] =  move.date 
                    

               
        return  super(stock_move, self).write(cr, uid, ids, vals, context=context)     

    def _get_gty_sing(self, cr, uid, ids, name, args, context=None):

        res = {}
        for m in self.browse(cr, uid, ids, context=context):
            coef = 0.0
            if m.location_id.usage != m.location_dest_id.usage: 
                if m.location_id.usage == 'internal':
                    coef = -1.0
                else:
                    if m.location_dest_id.usage  == 'internal':
                        coef = 1.0
            res[m.id] = m.product_qty * coef
        return res


    def _get_amount(self, cr, uid, ids, name, args, context=None):

        res = {}
        for m in self.browse(cr, uid, ids, context=context):
            amount = 0.0
            for quant in m.quant_ids:
                amount = amount + quant.cost * quant.qty
            res[m.id] = amount                                   # da si valori diferite de zero ???
        return res


    _columns = {
        'amount': fields.function(_get_amount, string='Amount', type='float', digits_compute=dp.get_precision('Account'), readonly=True, stored=True),
        'qty_sing': fields.function(_get_gty_sing, string="Quantity with Sing", type="float", digits_compute=dp.get_precision('Product Unit of Measure') )
    }


    _defaults = {
        'amount':  lambda *a: 0.0
    }

"""
    def create(self, cr, uid, vals, context={}):
        move_id = super(stock_move, self).create(cr, uid,  vals, context)
        for move in self.browse(cr, uid, [move_id], context):
            if move.amount == 0:
                self._get_reference_accounting_values_for_valuation(cr, uid, move)            
        return move_id



    def _get_reference_accounting_values_for_valuation(self, cr, uid, move, context=None):
        reference_amount, reference_currency_id = super(stock_move, self)._get_reference_accounting_values_for_valuation(cr, uid, move, context)
        self.write(cr, uid, [move.id], {'amount': reference_amount }, context=context)
        return reference_amount, reference_currency_id
"""



 
class stock_inventory(osv.osv):

    _inherit = 'stock.inventory'

    _columns = {
        'date': fields.datetime('Inventory Date', required=True, readonly=True, states={'draft': [('readonly', False)]}),
    }

    def prepare_inventory(self, cr, uid, ids, context=None):
        for inventory in self.browse(cr, uid, ids, context=context):
            date = inventory.date
            res = super(stock_inventory, self).prepare_inventory(cr, uid, ids, context)
            self.write(cr, uid, ids, { 'date': date})
        return res    
    
    def action_done(self, cr, uid, ids, context=None):
        super(stock_inventory,self).action_done(cr, uid, ids, context)
        for inv in self.browse(cr, uid, ids, context=context):
            for move in inv.move_ids:
                if move.date_expected != inv.date or move.date != inv.date   :
                    self.pool.get('stock.move').write(cr, uid, [move.id], { 'date_expected': inv.date, 'date':inv.date }, context )
        return True
 

"""

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"

    _columns = {
        'standard_price': fields.related('product_id','standard_price',type="float",relation="product.product",string="Standard Price",store=False)
    }
"""
 
 
class stock_production_lot(osv.osv):
    _inherit = 'stock.production.lot'
      
    '''
    def _get_active(self, cr, uid, ids, field_name, args, context=None): 
        res = {}
        for batch in self.browse(cr, uid, ids, context=context):
            res[batch.id] = not ( batch.stock_available == 0.0 )
        return res 
    '''
 
 
    def _get_stock(self, cr, uid, ids, field_name, arg, context=None):
        """ Gets stock of products for locations
        @return: Dictionary of values
        """
        if context is None:
            context = {}
        if 'location_id' not in context:
            locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')], context=context)
        else:
            locations = context['location_id'] and [context['location_id']] or []

        if isinstance(ids, (int, long)):
            ids = [ids]

        res = {}.fromkeys(ids, 0.0)
        if locations:
            cr.execute('''select
                    lot_id,
                    sum(qty)
                from
                    stock_quant
                where
                    location_id IN %s and lot_id IN %s group by lot_id''',(tuple(locations),tuple(ids),))
            res.update(dict(cr.fetchall()))

        return res

    def _stock_search(self, cr, uid, obj, name, args, context=None):
        """ Searches Ids of products
        @return: Ids of locations
        """
        locations = self.pool.get('stock.location').search(cr, uid, [('usage', '=', 'internal')])
        cr.execute('''select
                lot_id,
                sum(qty)
            from
                stock_quant
            where
                location_id IN %s group by lot_id
            having  sum(qty) '''+ str(args[0][1]) + str(args[0][2]),(tuple(locations),))
        res = cr.fetchall()
        ids = [('id', 'in', map(lambda x: x[0], res))]
        return ids 
 
            
    _columns = {
       'name': fields.char('Lot Number', size=64, required=True, help="Unique Lot Number, will be displayed as: PREFIX/SERIAL [INT_REF]"),         
       'active': fields.boolean('Active', help="By unchecking the active field, you may hide an Lot Number without deleting it."),
       'stock_available': fields.function(_get_stock, fnct_search=_stock_search, type="float", string="Available", select=True,
            help="Current quantity of products with this Serial Number available in company warehouses",
            digits_compute=dp.get_precision('Product Unit of Measure')),
    }

    _defaults = {
        'active': True,
    }

    _sql_constraints = [
        ('name_ref_uniq', 'unique (name,  product_id)', 'The combination of Lot Number and Product must be unique !'),
    ]

    def create(self, cr, uid, vals, context=None): 
        if context is None:
            context = {}
        prodlot_name = vals.get('name',False)
        lot_id = False
        if prodlot_name:
            product_id = vals.get('product_id',context.get('product_id',False))
            prodlot_ids = self.search(cr, uid, [('name', '=', prodlot_name),('product_id','=',product_id ),('active','=',False)], context=context)
            if len(prodlot_ids)==1:
                lot_id = prodlot_ids[0]
                self.write(cr, uid, [lot_id], {'active':True}, context)   # se reactiveaza un lot vechi
                
        if not lot_id:         
            lot_id = super(stock_production_lot, self).create(cr, uid, vals, context)
        return lot_id 


    def unlink(self, cr, uid, ids, context = {}):
        """Overwrites unlink method to avoid delete lots with moves"""
        
        ids_del = []
        for prodlot in self.browse(cr, uid, ids):
            move_ids = self.pool.get('stock.move').search(cr, uid, [('prodlot_id', '=', prodlot.id)])  #todo de cautat si in inventatul nepostat?
            if move_ids:
                if prodlot.stock_available == 0.0:
                    self.write(cr, uid, [prodlot.id], {'active':False}, context)   # se dezactiveaza lotul
                else:
                    raise osv.except_osv(_('Error !'), _('You cannot delete this lot because it has moves depends on!'))
            else:
                ids_del.append(prodlot.id)
        return super(stock_production_lot, self).unlink(cr, uid, ids_del, context = context)
        
     #TODO:De facut o rutina care sa dezactiveze    
stock_production_lot()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
