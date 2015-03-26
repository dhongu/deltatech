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



from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp




class stock_return_picking(models.TransientModel):
    _inherit = "stock.return.picking"

    make_new_picking = fields.Boolean(string="Make a new picking", default=True)

    @api.multi
    def _create_returns(self): 
        
        if self.make_new_picking: 
            new_picking_id, pick_type_id = super(stock_return_picking,self)._create_returns()
            
            record_id = self.env.context and self.env.context.get('active_id', False) or False
            pick = self.env['stock.picking'].browse(record_id)
            pick_return = self.env['stock.picking'].browse(new_picking_id)
            pick_backorder = pick_return.copy({
                                    'picking_type_id': pick.picking_type_id.id,
                                    'state': 'draft',
                                    'backorder_id':pick.id,
                                    'origin': pick.origin,
                                    'move_lines': [],
                                })
           
            pick_return.write({ 'origin': pick.origin})
            
            for move in pick_return.move_lines:
                move.write({'purchase_line_id':   move.origin_returned_move_id.purchase_line_id.id,})
                
                new_move= move.copy( {   'location_id':       move.origin_returned_move_id.location_id.id,
                                         'location_dest_id':  move.origin_returned_move_id.location_dest_id.id,
                                         'state':             'draft',
                                         'picking_id':        pick_backorder.id}) 
                
                new_move.write({'purchase_line_id':   move.origin_returned_move_id.purchase_line_id.id,})
 
            pick_backorder.action_confirm()
            pick_backorder.action_assign()
            
        return new_picking_id, pick_type_id
    
   
    
          
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
