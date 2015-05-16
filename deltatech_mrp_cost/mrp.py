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

from openerp.osv import osv
from openerp.osv import fields
from openerp.tools.translate import _
 
import openerp.pooler
import openerp.addons.decimal_precision as dp
from openerp import tools
from openerp import netsvc
from openerp.tools import float_compare



class mrp_production(osv.osv):
    _inherit = 'mrp.production'

    def _calculate_amount(self, cr, uid, ids, name, arg, context={}):
        res = {}
        for production in self.browse(cr, uid, ids, context=context):  
            res[production.id] = {'amount':0.0, 'calculate_price':0.0}
            
            calculate_price = 0.0
            amount = 0.0
            if not production.move_lines2:                
                for move in production.move_lines:
                    for quant in move.reserved_quant_ids:
                        if quant.qty > 0:
                            amount +=   quant.cost * quant.qty  # se face calculul dupa quanturile planificate
                calculate_price = amount / production.product_qty
                amount = 0.0          
            else:
                for move in production.move_lines2:
                    for quant in move.quant_ids:
                        if quant.qty > 0:
                            amount +=   quant.cost * quant.qty
                product_qty = 0.0
                for move in production.move_created_ids2:
                    product_qty += move.product_qty
                if product_qty == 0.0:
                    product_qty =   production.product_qty
                calculate_price = amount / product_qty  

            res[production.id]['calculate_price'] = calculate_price
            res[production.id]['amount'] = amount
        return res   

    _columns = {
        'amount': fields.function(_calculate_amount, multi='amount',  type='float',digits_compute= dp.get_precision('Account'),store=False, string='Production Amount'),
        'calculate_price': fields.function(_calculate_amount, multi='amount',  type='float',digits_compute= dp.get_precision('Product Price'),store=False, string='Calculate Price'),
    }

    def _get_raw_material_procure_method(self, cr, uid, product, location_id=False, location_dest_id=False, context=None):
        return "make_to_stock"

    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
        production = self.browse(cr, uid, production_id, context=context)
        #for move in production.move_lines:
        #    move.write({'procure_method' : 'make_to_stock'})
            
        if production.product_id.cost_method == 'real' and production.product_id.standard_price <> production.calculate_price:
            self.pool.get('product.product').write(cr,uid,[production.product_id.id],{'standard_price':production.calculate_price})
        
        res = super(mrp_production,self).action_produce(cr, uid, production_id, production_qty, production_mode, wiz, context)
        
        return res
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

