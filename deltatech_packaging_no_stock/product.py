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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from openerp.osv.fields import related

from openerp.addons.product import _common

_logger = logging.getLogger(__name__)


 
class product_template(models.Model):
    _inherit = 'product.template'
    
    pack_items = fields.Integer(string="Items per pack")

 
class packing_doc(models.Model):
    _name = 'packing.doc'
    _description = 'Packing Doc'
    _inherit = 'mail.thread'

    state = fields.Selection([
            ('draft','Draft'),
            ('done','Done'),
        ], string='Status', index=True, readonly=True, default='draft',   copy=False )  
    
    name = fields.Char(string="Name", readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    date = fields.Date(string='Date', readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    
    itme_ids = fields.One2many('packing.item',  'packing_doc_id', string='Packing Items',
                                readonly=True, states={'draft': [('readonly', False)]}, copy=True) 

    invoice_id = fields.Many2one('account.invoice', string='Invoice Reference', index=True,
                                readonly=True, states={'draft': [('readonly', False)]}, copy=True) 

    
    @api.multi
    def validate(self):
        return self.write( {'state': 'done'})    


    @api.multi
    def set_draft(self):
        return self.write( {'state': 'draft'}) 
    
    @api.model
    def create(self,   vals ):  
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence = self.env.ref('deltatech_packaging_no_stock.sequence_packing_doc')
            if sequence:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence.id)         
        return super(packing_doc, self).create( vals )  

    

class packing_item(models.Model):
    _name = 'packing.item'
    _description = "Packing Item"
    
    
    packing_doc_id = fields.Many2one('packing.doc', string="Packing Doc", ondelete='cascade', index=True)
    name = fields.Char(string='Pack')
    product_id = fields.Many2one('product.product', string='Product',required=True)
    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'), required=True, default=1)



    @api.model
    def create(self,   vals ):  
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence = self.env.ref('deltatech_packaging_no_stock.sequence_packing_item')
            if sequence:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence.id)         
        return super(packing_item, self).create( vals )      

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: