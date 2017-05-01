# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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



        
class sale_order_line(models.Model):
    _inherit = 'sale.order.line' 
    
    qty_available =  fields.Float( related= 'product_id.qty_available',string='Quantity On Hand')
    virtual_available = fields.Float(related='product_id.virtual_available', string='Quantity Available')

    qty_available_text = fields.Char(string="Available", compute='_compute_qty_available_text')

    @api.multi
    @api.depends('product_id', 'route_id')
    def _compute_qty_available_text(self):
        for line in self:
            product = line.product_id
            if line.route_id:
                location = False
                for pull in line.route_id.pull_ids:
                    location = pull.location_src_id
                if location:
                    product = line.product_id.with_context(location=location.id)
            qty_available_text = 'N/A'

            qty_available, virtual_available = product.qty_available, product.virtual_available
            outgoing_qty, incoming_qty = product.outgoing_qty, product.incoming_qty

            if qty_available or virtual_available or outgoing_qty or incoming_qty:
                qty_available_text = "%s = " % virtual_available
                if qty_available:
                    qty_available_text += ' +%s ' % qty_available
                if outgoing_qty:
                    qty_available_text += ' -%s ' % outgoing_qty
                if incoming_qty:
                    qty_available_text += ' +%s ' % incoming_qty

            line.qty_available_text = qty_available_text
