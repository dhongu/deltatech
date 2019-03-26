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



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp
import odoo
from psycopg2 import OperationalError

class procurement_order(models.Model):
    _inherit = 'procurement.order' 

    required_id = fields.Many2one('required.order', string='Required Products Order', index=True)
    proc_src_ids = fields.One2many('procurement.order', string='Source Procurement', compute='_compute_source_procurement'  )
    sale_id  = fields.Many2one('sale.order', related='sale_line_id.order_id',   string='Sale Order')
    
    @api.one
    def _compute_source_procurement(self):    
        self.proc_src_ids = self.search([('move_dest_id', 'in', [x.id for x in self.move_ids])])
        

    """
    def run(self, cr, uid, ids, autocommit=False, context=None):
        res = super(procurement_order, self).run(cr, uid, ids, autocommit, context)
        self.message_stock(cr, uid, ids, context)
        return res


    @api.multi
    def message_stock(self):      
        for procurement in self:
            if procurement.location_id.usage == 'internal':
                disp = procurement.product_id.with_context({'location': procurement.location_id.id})._product_available()[procurement.product_id.id]
                msg = _("When running was available quantity %s in location %s") % (str(disp['qty_available']), procurement.location_id.name)
                self.message_post( body= msg)            
        return
    """

 

    @api.model
    def _get_po_line_values_from_proc(self, procurement, partner, company, schedule_date):
        res = super(procurement_order, self)._get_po_line_values_from_proc(procurement, partner, company, schedule_date)
        
        seller_qty = procurement.product_id.seller_qty
        qty = procurement.product_qty
        if seller_qty and seller_qty > qty:
            msg = _("Required %s, but the Minimum order quantity is %s") % ( str(qty) , str(seller_qty) )
            procurement.message_post( body= msg)
        
        return res

    @api.model
    def _check(self,   procurement):
        if procurement.rule_id and procurement.rule_id.action == 'buy' and procurement.state == "running" and not procurement.purchase_id:
            msg = _("Purchase order was deleted")
            procurement.message_post( body= msg)
            procurement.write ({'state': 'cancel'} )
            return False

        picking_type_internal = self.env.ref('stock.picking_type_internal')
        
        # transferurile interne se vor forta pentru a fi cu make_to_stock
        msg = ''
        for move in procurement.move_ids:
            if move.picking_type_id and  move.picking_type_id.id == picking_type_internal.id:
                if move.procure_method=='make_to_order' and move.availability >= 0:
                    move.write({'procure_method':  'make_to_stock',
                                'state':'confirmed',
                                'move_orig_ids':[(6,0,[])]})   # nu se mai asteapata alte miscari si se va face transferul
                    msg = msg + _('Quantity %s is available from %s .\n') % (move.availability, move.product_qty  )
                    move.action_assign() 
        if msg:
            procurement.message_post( subject=_("Internal stock transfer"), body= msg)           

        res = super(procurement_order, self)._check( procurement) 
        
        if not res:
            if procurement.move_ids:
                done = True
                for move in procurement.move_ids:
                    done = done and (move.state == 'done')
                if done:
                    return True  
            else:
                if procurement.move_dest_id and procurement.move_dest_id.state == 'done':
                    return True
        if procurement.required_id:         
            procurement.required_id.check_order_done()
        return res
 
    @api.multi 
    def make_po(self):      
        res = super(procurement_order, self).make_po()
        uom_obj = self.pool.get('uom.uom')
        for procurement_id, po_line_id in res.iteritems():
            qty = 0
            po_line = self.env['purchase.order.line'].browse(po_line_id)
            seller_qty = po_line.product_id.seller_qty
            locations = self.env['stock.location']
            for procurement in po_line.procurement_ids:
                qty +=  uom_obj._compute_qty(self.env.cr, self.env.uid, from_uom_id=procurement.product_uom.id,
                                                              qty=procurement.product_qty, to_uom_id=procurement.product_id.uom_po_id.id)
                
            procurement = self.browse(procurement_id)    
            disp = procurement.product_id.with_context({'location': procurement.location_id.id})._product_available()[procurement.product_id.id]['qty_available']
            msg = _("It is necessary quantity %s and in stock is %s.") %   (str(qty), str(disp))  
            procurement.message_post( body= msg)  
            if  po_line.order_id.date_order < fields.Date.today() :
                msg = _("Acquisition should be done in the past at %s") %   (po_line.order_id.date_order)  
                procurement.message_post( body= msg)    
                po_line.order_id.write({'date_order':fields.Datetime.now()})                   
            """
            if disp > qty:
                po_line.unlink()
                #res.pop(procurement_id)
                msg = _("Necesar  %s si in stoc  %s. Deci nu e nevoie de alta achizitie.") %   (str(qty), str(disp))  
                procurement.message_post( body= msg)
                move = procurement.move_dest_id
                move.write({'procure_method':'make_to_stock', 'state':'assigned'})
                
                move.picking_id.recheck_availability()

            else:
                msg = _("Necesar  %s, Disp %s") %   (str(qty), str(disp))   
                procurement.message_post( body= msg)
                if disp > 0:
                    qty = qty - disp
            """
            """
            # si daca produsul are reorder point trebuie adaugat la qunat si cantitatea de reaprovizionat!!!
            #if seller_qty:
            #    qty = max(qty, seller_qty)
            #po_line.write({'product_qty':qty})
            """
        return res

    
    @api.model
    def _product_virtual_get(self, order_point):
        ''' trebuie sa scad toate comenzile de aprovizionare deschise'''  
        qty = super(procurement_order,self)._product_virtual_get(order_point)
        
        domain = [('product_id','=',order_point.product_id.id),
                  ('state','=','running'),
                  ('location_id','=',order_point.location_id.id)]
        
        procurement_ids = self.env['procurement.order'].search(domain)

        for procurement in procurement_ids:
            if procurement.rule_id.action == 'buy':
                qty += procurement.product_qty
         
        return qty


    def _procure_orderpoint_confirm(self, cr, uid, use_new_cursor=False, company_id = False, context=None):

        old_cr = cr
        if context is None:
            context = {}
        if use_new_cursor:
            cr = odoo.registry(cr.dbname).cursor()
        orderpoint_obj = self.pool.get('stock.warehouse.orderpoint')

        procurement_obj = self.pool.get('procurement.order')
        dom = company_id and [('company_id', '=', company_id)] or []
        orderpoint_ids = orderpoint_obj.search(cr, uid, dom)
         
         
        while orderpoint_ids:
            ids = orderpoint_ids[:100]
            
            del orderpoint_ids[:100]
            try:
                procurement_ids = procurement_obj.search(cr, uid, [('orderpoint_id','in',ids),('state','=','exception')])
                procurement_obj.cancel(cr, uid, procurement_ids)
                if use_new_cursor:
                    cr.commit()
            except:
                if use_new_cursor:
                    cr.rollback()
                    continue
                else:
                    raise
            
        res = super(procurement_order, self)._procure_orderpoint_confirm(old_cr, uid, use_new_cursor, company_id, context)
        
 
        if use_new_cursor:
            cr.commit()
            cr.close()         
        
        return res        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
