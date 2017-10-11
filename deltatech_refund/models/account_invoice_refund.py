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

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_TIME_FORMAT
import time 
from datetime import datetime

class account_invoice_refund(models.TransientModel):
    _inherit = "account.invoice.refund"

    @api.model
    def get_link(self, model ):
        for model_id, model_name in model.name_get():
            #link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name )
            link = "<a href=# data-oe-model=%s data-oe-id=%d>%s</a>" % (model._name, model_id, model_name)
        return link
    
    @api.multi
    def invoice_refund(self):
        res = super(account_invoice_refund,self).invoice_refund()
        for inv in self.env['account.invoice'].search(res['domain']):
            for picking in inv.origin_refund_invoice_id.picking_ids:
                
                if inv.type == 'in_refund':
                    if not picking.move_lines[0].purchase_line_id:  # recepte fara comanda de aprovizionare
                        default_make_new_picking = False
                    else:
                        default_make_new_picking = True                       
                elif inv.type == 'out_refund':
                    default_make_new_picking = False 
                    if self.filter_refund == 'refund':
                        Warning('Please make a new selection')   
                        # poate ca in aceasta situatie ar trebui sa refac legatura livrarii cu noua factura si sa nu mai anulez livrarea
                else:
                    raise  Warning('Use journal for refund ')   
                               
                # filter_refund: refund, cancel , modify
                 
                default_do_transfer = (self.filter_refund  != 'refund')
                                                
                return_obj = self.env['stock.return.picking'].with_context({'active_id':picking.id,
                                                                            'default_make_new_picking':default_make_new_picking,
                                                                            'default_do_transfer':default_do_transfer}).create({})
                # anularea miscarilor de stoc trebuie facut in functie de tipul de anulare                                                                 
                new_picking_id, pick_type_id  = return_obj._create_returns()

                new_picking = self.env['stock.picking'].browse(new_picking_id)
                new_picking.write({'invoice_id':inv.id,
                                   'invoice_state':'invoiced',})
                if new_picking.sale_id:
                    new_picking.sale_id.write( {'invoice_ids': [(4, inv.id)]})
                
                purchase = self.env['purchase.order']
                for move in new_picking.move_lines:
                    if move.purchase_line_id and move.purchase_line_id.order_id:
                        purchase  = purchase | move.purchase_line_id.order_id
                if purchase:
                    purchase.write( {'invoice_ids': [(4, inv.id)]})
                    
                # de vazut cum pun referinta facturii si in comanda de achizitie!
                msg = _('Picking list %s was refunded by %s') % (self.get_link(picking),  self.get_link(new_picking))                 
                inv.message_post(body=msg)

        return res
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: