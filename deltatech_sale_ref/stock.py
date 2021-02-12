# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from openerp.osv.fields import related
 
_logger = logging.getLogger(__name__)


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    ref = fields.Char(string="Reference", related="packop_id.ref" , copy=True)  #related=False

class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"
    
    ref = fields.Char(string="Reference", copy=True)
 
class stock_move(models.Model):
    _inherit = "stock.move"

    ref = fields.Char(string="Reference", related='procurement_id.sale_line_id.ref', copy=True)

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        if inv_type in ('out_invoice', 'out_refund') and move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id 
            res['ref'] = sale_line.ref
         
        return res
 

    @api.multi
    def _picking_assign(self, procurement_group, location_from, location_to):
        res = super(stock_move, self)._picking_assign( procurement_group, location_from, location_to)
        
        move_group_by_date = {}
        picking = self[0].picking_id
        for move in self:
            key = move.date[:10]
            move_group_by_date.setdefault(key, {'moves':self.env['stock.move'],'picking':False})
            
            move_group_by_date[key]['moves'] |=  move
            if picking:
                move_group_by_date[key]['picking'] = picking
            picking = False
       
        for key in move_group_by_date:
            moves = move_group_by_date[key]['moves']
            picking = move_group_by_date[key]['picking']
            if not picking:
                values = self._prepare_picking_assign(moves[0])
                picking = self.env["stock.picking"].create(values)
                moves.write({'picking_id': picking.id})

        

class stock_quant(models.Model):
    _inherit = "stock.quant"

    ref = fields.Char(string="Reference", related='history_ids.ref')
    
class stock_picking(models.Model):
    _inherit= "stock.picking"
    
   


    """
     de redefinit _prepare_pack_ops si  do_prepare_partial
     
    """
 
    # metoda redefiniat pentru a nu mai uni produsele care sunt din miscari diferite
    @api.cr_uid_ids_context
    def do_prepare_partial(self, cr, uid, picking_ids, context=None):
        context = context or {}
        pack_operation_obj = self.pool.get('stock.pack.operation')
        #used to avoid recomputing the remaining quantities at each new pack operation created
        ctx = context.copy()
        ctx['no_recompute'] = True

        #get list of existing operations and delete them
        existing_package_ids = pack_operation_obj.search(cr, uid, [('picking_id', 'in', picking_ids)], context=context)
        if existing_package_ids:
            pack_operation_obj.unlink(cr, uid, existing_package_ids, context)
        
        self.back_order_for_multi_prod(cr, uid, picking_ids, context=context)
            
        for picking in self.browse(cr, uid, picking_ids, context=context):
            
            picking_quants = []
            #Calculate packages, reserved quants, qtys of this picking's moves
            for move in picking.move_lines:
                forced_qties = {}  # Quantity remaining after calculating reserved quants
                if move.state not in ('assigned', 'confirmed', 'waiting'):
                    continue
                move_quants = move.reserved_quant_ids
                picking_quants += move_quants
                forced_qty = (move.state == 'assigned') and move.product_qty - sum([x.qty for x in move_quants]) or 0
                #if we used force_assign() on the move, or if the move is incoming, forced_qty > 0
                if float_compare(forced_qty, 0, precision_rounding=move.product_id.uom_id.rounding) > 0:
                    if forced_qties.get(move.product_id):
                        forced_qties[move.product_id] += forced_qty
                    else:
                        forced_qties[move.product_id] = forced_qty
                        
                for vals in self._prepare_pack_ops(cr, uid, picking, picking_quants, forced_qties, context=context):
                    if move.ref:
                        vals['ref'] = move.ref
                    pack_operation_obj.create(cr, uid, vals, context=ctx)
        #recompute the remaining quantities all at once
        self.do_recompute_remaining_quantities(cr, uid, picking_ids, context=context)
        self.write(cr, uid, picking_ids, {'recompute_pack_op': False}, context=context)


    @api.multi
    def back_order_for_multi_prod(self):
        """ Creare comanda restanta pentru produsele care se repeta"""
        for picking in self:
             cont = True
             sec_picking = False
             while cont:
                cont = False
                for move1 in picking.move_lines:
                    for move2 in picking.move_lines:
                        if move1.id != move2.id and move1.product_id.id == move2.product_id.id:
                            cont = True
                            if not sec_picking:
                                sec_picking = picking.copy({'backorder_id':picking.id,'move_lines':False})
                            move1.write({'picking_id':sec_picking.id})
                            
                
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: