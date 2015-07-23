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


class sale_order(models.Model):
    _inherit = 'sale.order' 
    
    
    procurement_count =  fields.Integer(string='Procurements',  compute='_compute_procurement_count')
    invoiced_rate = fields.Float(  compute='_compute_invoiced_rate' )  # string='Invoiced Ratio', exista acest camp dar este suprascris pt a apela alta metoda de calcul
    invoiced = fields.Boolean(compute='_compute_invoiced' )

    @api.one
    @api.depends('order_line.procurement_ids' )
    def _compute_procurement_count(self):           
        value = 0 
        procurements = self.env['procurement.order']
        for sale in self:
            for line in sale.order_line:
                for procurement in line.procurement_ids:
                    procurements = procurements | procurement 
                 
        self.procurement_count = len(procurements)


    @api.one
    @api.depends('invoice_ids.amount_untaxed', 'amount_untaxed')
    def _compute_invoiced_rate(self):   
        if self.currency_id:
            to_currency = self.currency_id
        else:
            to_currency = self.env.user.company_id.currency_id
 
        if self.amount_untaxed:   
            invoice_tot = 0.0     
            for invoice in self.invoice_ids:
                if invoice.state not in ('draft','cancel'):
                    if invoice.currency_id:
                        from_currency = invoice.currency_id.with_context(date=invoice.date_invoice)
                    else:    
                        from_currency = self.env.user.company_id.currency_id.with_context(date=invoice.date_invoice)
                    value = invoice.amount_untaxed
                    if  invoice.type == 'out_refund' :
                        value = -value
                          
                    invoice_tot += from_currency.compute(value, to_currency )
                    
            self.invoiced_rate =   min(100.00, invoice_tot * 100.0 / (self.amount_untaxed or 1.00))
        else:
            self.invoiced_rate = 0.0
        
    # todo: sa tina cont si de facturile rambursate
    @api.one
    @api.depends('invoice_ids')
    def _compute_invoiced(self):
        self.invoiced = False
        for invoice in self.invoice_ids:
            if invoice.state =='paid':
                self.invoiced = True


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
            for line in order.order_line:
                procurement_ids += [procurement.id for procurement in line.procurement_ids]

        action['context'] = {}
         
        if len(procurement_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, procurement_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'procurement', 'procurement_form_view')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = procurement_ids and procurement_ids[0] or False
        return action      
    
    def view_to_be_delivered(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing move  .
        '''
        if context is None:
            context = {}
        mod_obj = self.pool.get('ir.model.data')
        dummy, action_id = tuple(mod_obj.get_object_reference(cr, uid, 'stock', 'action_move_form2'))
        action = self.pool.get('ir.actions.act_window').read(cr, uid, action_id, context=context)

        move_ids = []
        for order in self.browse(cr, uid, ids, context=context):
            for line in order.order_line:
                for procurement in line.procurement_ids:
                    move_ids += [move.id for move in procurement.move_ids if move.state in ['assigned','waiting','confirmed'] ]

        action['context'] = {}
         
        if len(move_ids) >= 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, move_ids)) + "])]"
        else:
            res = mod_obj.get_object_reference(cr, uid, 'stock', 'action_move_form2')
            action['views'] = [(res and res[1] or False, 'form')]
            action['res_id'] = move_ids and move_ids[0] or False
        return action 
 
    def action_ship_create(self, cr, uid, ids, context=None):
        """
         from https://github.com/aliomattux/auto_check_availability/blob/master/models/stock.py
        """
        picking_obj = self.pool.get('stock.picking')
        res = super(sale_order, self).action_ship_create(cr, uid, ids, context=context)
        
        for order in self.browse(cr, uid, ids):
            for picking in order.picking_ids:
                if picking.state == 'confirmed':
                    picking_obj.action_assign(cr, uid, picking.id)

        return res

    @api.multi
    def open_sale_order(self):
        
        url =  "web?=#id="+str(self.id)+"&view_type=form&model=sale.order"
        
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
            }
    
    @api.multi
    def action_button_confirm_to_invoice(self): 
        if self.state == 'draft':     
            self.action_button_confirm()  # confirma comanda
        for picking in self.picking_ids:
            picking.action_assign()   # verifica disponibilitate
            if not all(move.state == 'assigned' for move in picking.move_lines):
                raise Warning(_('Not all products are available. ')   )
            picking.do_transfer()
  
        action_obj = self.env.ref('stock_account.action_stock_invoice_onshipping')
        action = action_obj.read()[0]

        action['context'] =  {'active_ids': self.picking_ids.ids, 'active_id': self.picking_ids[0].id  } 
        return   action

        
class sale_order_line(models.Model):
    _inherit = 'sale.order.line' 
    
    qty_available =  fields.Float( related= 'product_id.qty_available',string='Quantity On Hand')
    virtual_available = fields.Float(  related= 'product_id.virtual_available' , string='Quantity Available' )     


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
