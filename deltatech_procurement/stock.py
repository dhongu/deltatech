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


class stock_move(models.Model):
    _inherit = 'stock.move'
    
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
