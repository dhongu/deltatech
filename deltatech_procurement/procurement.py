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


class procurement_order(models.Model):
    _inherit = 'procurement.order' 

    required_id = fields.Many2one('required.order', string='Required Products Order', index=True)
    proc_src_ids = fields.One2many('procurement.order', string='Source Procurement', compute='_compute_source_procurement'  )


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
            procurement.write ({'state': 'cancel'} )
            return False
        res = super(procurement_order, self)._check( procurement)
        if procurement.required_id:         
            procurement.required_id.check_order_done()
        return res
 
    @api.multi 
    def make_po(self):      
        res = super(procurement_order, self).make_po()
        uom_obj = self.pool.get('product.uom')
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
            msg = _("Necesar  %s si in stoc  %s.") %   (str(qty), str(disp))  
            procurement.message_post( body= msg)            
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
            # si daca produsul are reorder point trebuie adaugat la qunt si cantitatea de reaprovizionat!!!
            #if seller_qty:
            #    qty = max(qty, seller_qty)
            #po_line.write({'product_qty':qty})
            """
        return res
        


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
