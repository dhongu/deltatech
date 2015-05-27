# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com 
#                    Kyle Waid  <kyle.waid(@)gcotech(.)com
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


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.model
    def default_get(self, fields ):

        res = super(stock_picking, self).default_get(  fields )
        if not res.get('picking_type_id', False):
            context = self.env.context
            if context is None: context = {}
            default_picking_type_code = context.get('default_picking_type_code', [])
            
            try:            
                if default_picking_type_code == 'incoming':
                    picking_type = self.env.ref('stock.picking_type_in')
               
                elif default_picking_type_code == 'outgoing':
                    picking_type = self.env.ref('stock.picking_type_out')
    
                elif default_picking_type_code == 'internal':
                    picking_type = self.env.ref('stock.picking_type_internal')

                elif default_picking_type_code == 'consume':
                    picking_type = self.env.ref('stock.picking_type_consume')    
                                
                if picking_type: 
                    res['picking_type_id'] = picking_type.id
            except:
                pass
        return res

    
    @api.multi
    def rereserve_pick(self):
        res = super(stock_picking, self).rereserve_pick()
        for picking in self:
            for move in picking.move_lines:
                if move.state == 'waiting' and move.availability >= 0:
                    """
                    if round(move.availability, 2) < round(move.product_qty, 2):
                        move_new_id = self.env['stock.move'].split( move=move, qty=move.availability)  
                        move_new = self.browse([move_new_id])
                        move.write({'availability':  0})
                    else:
                    """                    
                    move.write({'procure_method':  'make_to_stock',
                                'state':'confirmed',
                                'move_orig_ids':[(6,0,[])]})
                    #move.do_unreserve()
                    move.action_assign()
                                                            
        return res

    @api.cr_uid_ids_context
    def do_enter_receipt_details(self, cr, uid, picking, context=None):
        return self.do_enter_transfer_details(cr,uid,picking, context )
        
    @api.cr_uid_ids_context
    def do_enter_delivery_details(self, cr, uid, picking, context=None):
        return self.do_enter_transfer_details(cr,uid,picking, context )


    def do_print_picking(self, cr, uid, ids, context=None):
        '''
            This function prints the picking list
            Trebuie tiparit  fiecare document pe formularul lui!
            - Bon de consum -
            - Aviz de expeditie - cu/fara pret
            - Transter intre gestiuni
            - Intrare marfa in stoc ???
        
        '''
        
        context = dict(context or {}, active_ids=ids)       
        return self.pool.get("report").get_action(cr, uid, ids, 'stock.report_picking', context=context)


class stock_move(models.Model):
    _inherit = 'stock.move'
    
       
        
    
    @api.multi
    def do_make_to_stock(self):
        for move in self:
            if move.product_qty > 0 and move.procure_method == 'make_to_order' and round(move.availability, 2) >= round(move.product_qty, 2):
                procurement = self.env['procurement.order'].search([('move_dest_id','=',move.id)])
                if procurement:
                    procurement.cancel() 
                move.procure_method = 'make_to_stock'  
                  
    

    def action_assign(self, cr, uid, ids, context=None):
        #self.do_make_to_stock(cr, uid, ids, context)
        return super(stock_move, self).action_assign(cr, uid, ids, context)



    def action_confirm(self, cr, uid, ids, context=None):
        """
        from https://github.com/aliomattux/make_to_order_check_availability/blob/master/models/stock.py
        """
        #self.do_make_to_stock(cr, uid, ids, context)
        return super(stock_move, self).action_confirm(cr, uid, ids, context)

    
    def _prepare_procurement_from_move(self, cr, uid, move, context=None):
        move_obj = self.pool.get('stock.move')
        def get_parent_move(move_id):
            move = move_obj.browse(cr, uid, move_id)
            if move.move_dest_id:
                return get_parent_move(move.move_dest_id.id)
            return move_id
        
        res = super(stock_move,self)._prepare_procurement_from_move(cr, uid, move, context)
        parent_move_line = get_parent_move(move.id)
        if parent_move_line:
            move = move_obj.browse(cr, uid, parent_move_line)
            partner_name = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.partner_id.name or False
            name = move.procurement_id and move.procurement_id.sale_line_id and move.procurement_id.sale_line_id.order_id.name or False
            if partner_name:
                res['origin'] = name + ':' +partner_name
        return res
    
    """
    def _create_procurement(self, cr, uid, move, context=None):
        procurement_id = super(stock_move,self)._create_procurement(cr, uid, move, context)
        procurement_obj = self.pool.get('procurement.order')
        
        msg = _("Necesarul a fot generat de miscarea %s") % ( move.picking_id.name)
        procurement_obj.message_post(cr, uid, [procurement_id], body = msg, context=context)
       
        return procurement_id
    """
    
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
