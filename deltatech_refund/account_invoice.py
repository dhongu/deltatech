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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_TIME_FORMAT
import time 
from datetime import datetime

class account_invoice(models.Model):
    _inherit = "account.invoice"

    # camp pt a indica din ce factura se face stornarea
    origin_refund_invoice_id = fields.Many2one('account.invoice', string='Origin Invoice',   copy=False)
    # camp prin care se indica prin ce factura se face stornarea 
    refund_invoice_id = fields.Many2one('account.invoice', string='Refund Invoice',    copy=False)
   
    @api.model
    def get_link(self, model ):
        for model_id, model_name in model.name_get():
            link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name )
        return link
    
         
    @api.multi
    @api.returns('self')
    def refund(self, date=None, period_id=None, description=None, journal_id=None):
        new_invoices = super(account_invoice, self).refund(date, period_id, description,journal_id )
        new_invoices.write({'origin_refund_invoice_id':self.id})
        self.write({'refund_invoice_id':new_invoices.id})
        msg = _('Invoice %s was refunded by %s') % (self.get_link(self),  self.get_link(new_invoices))
        self.message_post(body=msg)
        new_invoices.message_post(body=msg)
        return new_invoices         


    @api.multi
    def unlink(self):
        for invoice in self:
            for picking in invoice.picking_ids:
                picking.write({'invoice_state':'2binvoiced'})
            
        res = super(account_invoice, self).unlink()
        return res
    
    
    
class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _create_invoice_line_from_vals(self,  move, invoice_line_vals ):
        invoice_line_id = super(stock_move, self)._create_invoice_line_from_vals(  move, invoice_line_vals  )
        move.picking_id.write({'invoice_id': invoice_line_vals['invoice_id']})
        return invoice_line_id
        
        
        
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



 
