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
from openerp import models, fields, api
from openerp import pooler
import time
from openerp.osv import fields, osv, orm
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class stock_transfer(models.TransientModel):
    _name = 'deltatech.stock.transfer'
    _description = 'Stock Transfer'

    _columns = {
        'location_id': fields.many2one('stock.location', 'Source Location', required=True ),   
        'date': fields.datetime('Date'),
        'product_id': fields.many2one('product.product', 'Product', required=True, select=True, domain=[('type','<>','service')]),   
        'product_dest_id': fields.many2one('product.product', 'Product Destination', required=True, select=True, domain=[('type','<>','service')]),   
        'product_qty': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),                                      
        'product_uom': fields.many2one('product.uom', 'Unit of Measure' ),        
        'lot_id': fields.many2one('stock.production.lot', 'Serial Number'),
        'lot_dest_id': fields.many2one('stock.production.lot', 'Serial Number Destination'),
        'picking_type_id': fields.many2one('stock.picking.type', 'Picking Type', required=True),
    }


    def default_get(self, cr, uid, fields, context):
        """ To get default values for the object.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param fields: List of fields for which we want default values
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
         
        res = super(stock_transfer, self).default_get(cr, uid, fields, context=context)

        if 'date' in fields:
            res.update({'date': time.strftime('%Y-%m-%d %H:%M:%S')})
        if 'location_id' in fields:
            try:
                model, location_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'stock_location_stock')
                self.pool.get('stock.location').check_access_rule(cr, uid, [location_id], 'read', context=context)
            except (orm.except_orm, ValueError):
                location_id = False
            res.update({'location_id': location_id})
        return res


    def onchange_product_id(self, cr, uid, ids, prod_id=False, prodlot_id=False, loc_id=False, to_date=False   ):
        if not prod_id:
            return {'value': {'product_qty': 0.0, 'product_uom': False}}
        obj_product = self.pool.get('product.product').browse(cr, uid, prod_id)
        uom_id = obj_product.uom_id.id
        
        ctx = {}
        ctx.update({
            'states': ['done'],
            'location': [loc_id],
            'lot_id':prodlot_id
        })
        
        if prodlot_id :
            ctx['lot_id'] = prodlot_id
        
        amount = self.pool.get('product.product')._product_available(cr, uid, [prod_id], context=ctx)
  
        result = {'product_qty': amount[prod_id]['qty_available'], 'product_uom': uom_id,  'product_dest_id':prod_id, 'lot_dest_id':prodlot_id}        
        return {'value': result}




    def do_transfer(self, cr, uid, ids, context=None):
        
        move_obj = self.pool.get('stock.move')
        picking_obj = self.pool.get('stock.picking')
        
        model, location_inv_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'stock', 'location_inventory')
        
        transfer_data = self.browse(cr, uid,ids[0]) 
        
        name = self.pool.get('ir.sequence').next_by_code(cr, uid, 'stock.picking')
        
        move_val1 = {
                     'name': name or '',
                     'product_id':transfer_data.product_id.id,
                     'product_uom_qty':transfer_data.product_qty,
                     'product_uom':transfer_data.product_uom.id,
                     'location_id':transfer_data.location_id.id,
                     'restrict_lot_id':transfer_data.lot_id.id,
                     'location_dest_id':location_inv_id,
                     'date':transfer_data.date,
                     'date_expected':transfer_data.date,
                     'state': 'assigned',
                     }
        move_val2 = {
                    'name': name or '',
                     'product_id':transfer_data.product_dest_id.id,
                     'product_uom_qty':transfer_data.product_qty,
                     'product_uom':transfer_data.product_uom.id,
                     'location_id':location_inv_id,
                     'restrict_lot_id':transfer_data.lot_dest_id.id,
                     'location_dest_id':  transfer_data.location_id.id,
                     'date_expected':transfer_data.date,
                     'date':transfer_data.date,
                     'state': 'assigned',
                     }
        picking_val = {'date':transfer_data.date,
                       'name': name or '', 
                       'picking_type_id': transfer_data.picking_type_id.id,
                       'move_lines':[(0,0,move_val1),(0,0,move_val2)],
                       }
        picking_id = picking_obj.create(cr, uid, picking_val, context)
        picking = picking_obj.browse(cr, uid, picking_id, context=context)
              
        move_obj.action_done(cr, uid, [x.id for x in picking.move_lines]  , context=context) 
        

        return {
            'domain': "[('id','in', ["+str(picking_id)+"])]",
            'name': _('Stock Transfer'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: