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


class required_order(models.Model):
    _name = 'required.order'
    _description = "Required Products Order"
    _inherit = 'mail.thread'

    name = fields.Char(string='Reference',  index=True, readonly=True,  states={'draft': [('readonly', False)]},   copy=False)
    
    state = fields.Selection([
            ('draft','Draft'),
            ('progress', 'Confirmed'),
            ('cancel', 'Canceled'),
            ('done', 'Done'),
        ], string='Status', index=True, readonly=True, default='draft', copy=False )  

    
    required_line = fields.One2many('required.order.line', 'required_id', string='Required Lines', readonly=True, states={'draft': [('readonly', False)]} )   
    date_planned  = fields.Datetime(string='Scheduled Date',required=True, readonly=True, states={'draft': [('readonly', False)]} ,
                                    default=fields.Datetime.now() )
    location_id   = fields.Many2one('stock.location', required=True,string='Procurement Location', readonly=True, states={'draft': [('readonly', False)]} ) 
    group_id =  fields.Many2one('procurement.group', string='Procurement Group',readonly=True )

    route_id  = fields.Many2one('stock.location.route',  string='Route', readonly=True, states={'draft': [('readonly', False)]}   ) 
 
    warehouse_id = fields.Many2one('stock.warehouse', required=True,string='Warehouse', readonly=True, states={'draft': [('readonly', False)]},
                                    help="Warehouse to consider for the route selection")


    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):     
        self.location_id = self.warehouse_id.lot_stock_id

     
    _defaults = {      
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'required.order'),
     }
 
    @api.multi
    def order_done(self):
        return self.write({'state': 'done'})
           
            
            
    @api.multi
    def order_confirm(self):
        for order in self:
            group =  self.env['procurement.group'].create({'name':order.name})
            order.write({'group_id':group.id})
             
            
            procurement = order.required_line.create_procurement()   
            picking_vals = {
                'picking_type_id': procurement.rule_id.picking_type_id.id,
                'date': order.date_planned,
                'origin': order.name,
                'state': 'draft',
            }
            picking = self.env['stock.picking'].create(picking_vals)
            
            for line in order.required_line:
                move_vals = {
                    'name':line.product_id.name or '',
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'picking_id': picking.id,
                    'location_id':  procurement.rule_id.location_src_id.id or  
                                    procurement.rule_id.picking_type_id.default_location_src_id.id, 
                    'location_dest_id': order.location_id.id,
                    'picking_type_id': procurement.rule_id.picking_type_id.id,
                    'group_id': group.id,
                    'procurement_id': line.procurement_id.id, 
                    'origin': order.name,
                    'warehouse_id': order.warehouse_id.id,
                    'invoice_state': 'none'                 
                }
 
                move = self.env['stock.move'].create(move_vals)
                
            picking.action_confirm()
            picking.action_assign()       
        return self.write( {'state': 'progress'})
 
    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete a order  which is not draft or cancelled. '))
        return super(required_order, self).unlink() 
 
class required_order_line(models.Model):
    _name = 'required.order.line'
    _description = "Required Products Order Line"   
          
    required_id = fields.Many2one('required.order', string='Required Products Order', ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='set null'  )
    product_qty = fields.Float(string='Quantity',   digits= dp.get_precision('Product Unit of Measure'))
    procurement_id =  fields.Many2one('procurement.order', string='Procurement Order')
    
    
    @api.multi
    def create_procurement(self):
        procurement = self.env['procurement.order']
        for line in self:
            order = line.required_id
            procurement = self.env['procurement.order'].create({
                    'name': line.product_id.name,
                    'origin': order.name,
                    'date_planned': order.date_planned,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'warehouse_id': order.warehouse_id.id,
                    'location_id': order.location_id.id, 
                    'group_id': order.group_id.id,
                    'route_ids':[(6,0,[order.route_id.id])]
                })
            #procurement.run()
            #if not procurement.rule_id:
                #raise  Warning(_('Role not found!'))
            
            line.write({'procurement_id':procurement.id})
        return procurement
        
    
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
