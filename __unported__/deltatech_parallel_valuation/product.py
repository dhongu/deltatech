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

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment

    
    
class ProductTemplate(models.Model):
    _inherit = "product.template"   
 
         

    list_price_currency_id = fields.Many2one('res.currency',  string='Currency List Price', help="Currency for list price." , compute='_compute_currency_id' )
    cost_price_currency_id = fields.Many2one('res.currency',  string='Currency Cost Price ', help="Currency for cost price.",  compute='_compute_currency_id'  )


    @api.one
    def _compute_currency_id(self):           
 
        price_type = self.env['product.price.type'].search([('field','=','list_price')]) 
        if price_type:
            self.list_price_currency_id = price_type.currency_id
        else:
            self.list_price_currency_id = self.env.user.company_id.currency_id
        
        price_type = self.env['product.price.type'].search([('field','=','standard_price')]) 
        if price_type:
            self.cost_price_currency_id = price_type.currency_id
        else:
            self.cost_price_currency_id = self.env.user.company_id.currency_id
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





