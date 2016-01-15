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

from openerp import models, fields, api, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment

 
class stock_quant(models.Model):
    _inherit = "stock.quant"   
    
    inventory_value = fields.Float(store=True)    
    categ_id = fields.Many2one('product.category',string='Internal Category',related="product_id.categ_id", store=True)  
    customer_id = fields.Many2one('res.partner',string='Customer')
    supplier_id = fields.Many2one('res.partner',string='Supplier')
    origin =  fields.Char(string='Source Document')


class stock_move(models.Model):
    _inherit = "stock.move"  

    @api.multi
    def update_quant_partner(self):
        for move in self:
            if move.picking_id and move.picking_id.partner_id:
                if move.location_dest_id.usage == 'customer':
                    move.quant_ids.write({'customer_id':move.picking_id.partner_id.id,
                                          'origin':move.picking_id.origin})
                if move.location_dest_id.usage  == 'supplier': 
                    move.quant_ids.write({'supplier_id':move.picking_id.partner_id.id,
                                          'origin':move.picking_id.origin})
                
    @api.multi
    def action_done(self):
        res = super(stock_move,self).action_done()
        self.update_quant_partner()
        return res
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





