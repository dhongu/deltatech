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

    _track = {
        'state': {
            'deltatech_procurement.mt_order_confirmed': lambda self, cr, uid, obj, ctx=None: obj.state in ['progress'],
            'deltatech_procurement.mt_order_done': lambda self, cr, uid, obj, ctx=None: obj.state in ['done']
        },
    }



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
    
    procurement_count =  fields.Integer(string='Procurements',  compute='_compute_procurement_count')

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
        return self.write( {'state': 'progress'})
 
    @api.multi
    def unlink(self):
        for order in self:
            if order.state not in ('draft', 'cancel'):
                raise Warning(_('You cannot delete a order which is not draft or cancelled. '))
        return super(required_order, self).unlink() 
    
    
    @api.multi
    def check_order_done(self):
        for order in self:
            is_done = True
            for line in order.required_line:
                if line.procurement_id.state != "done":
                    is_done = False
            if is_done:
                order.order_done()
            
    @api.one
    @api.depends('required_line.procurement_id' )
    def _compute_procurement_count(self):           
        value = 0 
        procurements = self.env['procurement.order']
        for order in self:
            for line in order.required_line:
                procurements = procurements | line.procurement_id 
                 
        self.procurement_count = len(procurements)




    def view_procurement(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing procurement of given purchase order ids.
        '''
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        dummy, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'procurement', 'procurement_action'))
        action = self.pool.get('ir.actions.act_window').read(cr, uid, action_id, context=context)

        procurement_ids = []
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.required_line:
                procurement_ids += [line.procurement_id.id] 

        action['context'] = {}
         
        if len(procurement_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, procurement_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'procurement', 'procurement_form_view')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = procurement_ids and procurement_ids[0] or False
        return action     
 
class required_order_line(models.Model):
    _name = 'required.order.line'
    _description = "Required Products Order Line"   
    
       
    required_id = fields.Many2one('required.order', string='Required Products Order', ondelete='cascade', index=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='set null'  )
    product_qty = fields.Float(string='Quantity',   digits= dp.get_precision('Product Unit of Measure'))
    procurement_id =  fields.Many2one('procurement.order', string='Procurement Order')
    note = fields.Char(string='Note') 
    
    @api.multi
    def create_procurement(self):
        procurement = self.env['procurement.order']
        for line in self:
            order = line.required_id
            values = {
                    'name': line.note or line.product_id.name,
                    'origin': order.name + ':' + order.location_id.name,
                    'date_planned': order.date_planned,
                    'product_id': line.product_id.id,
                    'product_qty': line.product_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'warehouse_id': order.warehouse_id.id,
                    'location_id': order.location_id.id, 
                    'group_id': order.group_id.id,
                    'required_id':order.id,
                }

            if order.route_id:
                values['route_ids'] = [(6,0,[order.route_id.id])]
                
            
            procurement = self.env['procurement.order'].create(values)
            procurement.run()
            if not procurement.rule_id:
                raise  Warning(_('Role not found for product %s!') % line.product_id.name )
            
            line.write({'procurement_id':procurement.id})
        return procurement
        
    
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
