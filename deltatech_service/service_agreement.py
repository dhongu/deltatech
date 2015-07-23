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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class service_agreement (models.Model):
    _name = 'service.agreement'
    _description = "Contract Services"
    _inherit = 'mail.thread'
    
    name = fields.Char(string='Reference', index=True, readonly=True, states={'draft': [('readonly', False)]}, copy=False)
   
    description = fields.Char(string='Description',   readonly=True, states={'draft': [('readonly', False)]}, copy=False)
    
    date_agreement = fields.Date(string='Agreement Date',
        readonly=True, states={'draft': [('readonly', False)]},  copy=False)
    
    partner_id = fields.Many2one('res.partner', string='Partner', 
        required=True, readonly=True, states={'draft': [('readonly', False)]})
    
    agreement_line = fields.One2many('service.agreement.line', 'agreement_id', string='Agreement Lines',
       readonly=True, states={'draft': [('readonly', False)]}, copy=True)  

    state = fields.Selection([
            ('draft','Draft'),
            ('open','In Progress'),
            ('closed','Terminated'),
        ], string='Status', index=True, readonly=True, default='draft',   copy=False )    


    @api.multi
    def contract_close(self):
        return self.write({'state': 'closed'})

    @api.multi
    def contract_open(self):
        return self.write( {'state': 'open'})

    @api.multi
    def contract_draft(self):
        return self.write( {'state': 'draft'})    
 
class service_agreement_line(models.Model):
    _name = 'service.agreement.line'
    _description = "Service Agreement Line"  


    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id


    agreement_id = fields.Many2one('service.agreement', string='Contract Services' , ondelete='cascade')   
    product_id = fields.Many2one('product.product', string='Product', ondelete='set null', domain=[('type', '=', 'service')] )
    quantity = fields.Float(string='Quantity',   digits= dp.get_precision('Product Unit of Measure'))
    quantity_free = fields.Float(string='Quantity Free',   digits= dp.get_precision('Product Unit of Measure'))
    price_unit = fields.Float(string='Unit Price', required=True, digits= dp.get_precision('Product Price'),  default=1)  
    currency_id = fields.Many2one('res.currency', string="Currency", required=True, default=_default_currency,
                                  domain=[('name', 'in', ['RON','EUR'])])   
    
  
  
    @api.onchange('product_id')
    def onchange_product_id(self):
        price_unit = self.product_id.list_price
        self.price_unit = self.env.user.company_id.currency_id.compute(price_unit, self.currency_id )
    

    @api.model
    def get_value_for_consumption(self):
          cons_value = {
                      'product_id':  self.product_id.id,    
                      'quantity:':   self.quantity, 
                      'price_unit':  self.price_unit,
                      'currency_id': self.currency_id.id
                }
          return  cons_value


class account_invoice(models.Model):
    _inherit = 'account.invoice'
    agreement_id = fields.Many2one('service.agreement', string='Contract Services' ) 
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: 