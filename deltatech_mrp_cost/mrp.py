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

from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    amount = fields.Float(digits = dp.get_precision('Account'), string='Production Amount', 
                          compute='_calculate_amount')
    calculate_price = fields.Float(digits = dp.get_precision('Account'), string='Calculate Price', readonly=False, store=True)
 
 
    @api.multi
    def compute_price(self):
         
        for production in self:
            calculate_price, amount = production._compute_amount()
            production.write({'calculate_price':calculate_price,  'amount':amount})
            production.onchange_calculate_price() 


    @api.onchange('calculate_price')
    def onchange_calculate_price(self):
        for production in self:
            if production.product_id.cost_method == 'real' and production.product_id.standard_price <> production.calculate_price:
                    production.product_id.write( {'standard_price':production.calculate_price})

    @api.multi
    def _compute_amount(self):
        self.ensure_one()
        production = self  
        calculate_price = 0.0
        amount = 0.0
        if not production.move_lines2:                
            for move in production.move_lines:
                if move.reserved_quant_ids:
                    for quant in move.reserved_quant_ids:
                        if quant.qty > 0:
                            amount +=   quant.cost * quant.qty  # se face calculul dupa quanturile planificate
                else:
                    amount += move.product_id.standard_price * move.product_uom_qty
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
     
        return calculate_price, amount

    @api.multi
    def _calculate_amount(self ):
        for production in self:
            production.calculate_price, production.amount = production._compute_amount() 




    def _get_raw_material_procure_method(self, cr, uid, product, location_id=False, location_dest_id=False, context=None):
        return "make_to_stock"

    
    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
        production = self.browse(cr, uid, production_id, context=context)
            
        if production.product_id.cost_method == 'real' and production.product_id.standard_price <> production.calculate_price:
            self.pool.get('product.product').write(cr,uid,[production.product_id.id],{'standard_price':production.calculate_price})
        
        res = super(mrp_production,self).action_produce(cr, uid, production_id, production_qty, production_mode, wiz, context)

        self.assign_picking(cr, uid, [production_id], context)
                    
        return res

 
    @api.multi
    def assign_picking(self):

        for production in self:
            """
            Totate produsele consumate se vor reuni intr-un picking list 
            """            
            move_list = self.env['stock.move']
            for move in production.move_lines2:
                if not move.picking_id:
                    move_list += move
            if move_list:
                picking_type = self.env.ref('stock.picking_type_consume_for_production',raise_if_not_found=False)
                
                if picking_type: 
                    picking = self.env['stock.picking'].create({'picking_type_id':picking_type.id,
                                                                'date':production.date_planned,
                                                                'origin':production.name})                    
                    move_list.write({'picking_id':picking.id})
                    picking.get_account_move_lines()
       
            """
            Totate produsele receptionte  se vor reuni intr-un picking list?? 
            """
            move_list = self.env['stock.move']
            for move in production.move_created_ids2:
                if not move.picking_id:
                    move_list += move
            if move_list:
                picking_type = self.env.ref('stock.picking_type_receipt_for_production',raise_if_not_found=False)
                
                if picking_type: 
                    picking = self.env['stock.picking'].create({'picking_type_id':picking_type.id,
                                                                'date':production.date_planned,
                                                                'origin':production.name})                    
                    move_list.write({'picking_id':picking.id})
                    picking.get_account_move_lines()
        
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

