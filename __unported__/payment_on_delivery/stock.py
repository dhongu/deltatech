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
#
##############################################################################

 
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare



class stock_picking(models.Model):
    _inherit = 'stock.picking'

   
    @api.model 
    def _create_invoice_from_picking(self,  picking, vals):        
        invoice_id = super(stock_picking, self)._create_invoice_from_picking( picking, vals)
        
        if picking.sale_id and  picking.sale_id.payment_acquirer_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            invoice.write({'payment_acquirer_id':picking.sale_id.payment_acquirer_id.id})
         
        return invoice_id
 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
