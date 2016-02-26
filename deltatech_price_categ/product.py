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
from openerp.exceptions import except_orm, ValidationError, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
 


class product_template(models.Model):
    _inherit = 'product.template'


    list_price_base   = fields.Selection([('list_price','List price'),('standard_price', 'Cost Price')],string = 'Base Price', default="standard_price")
    
    percent_bronze    = fields.Float(string="Bronze Percent")
    percent_silver    = fields.Float(string="Silver Percent")
    percent_gold      = fields.Float(string="Gold Percent")
    
    list_price_bronze = fields.Float(string="Bronze Price",compute="_compute_price",store=True, readonly=True)
    list_price_silver = fields.Float(string="Silver Price",compute="_compute_price",store=True, readonly=True)
    list_price_gold   = fields.Float(string="Gold Price",compute="_compute_price",store=True, readonly=True)


 


    @api.multi
    @api.depends('list_price_base','standard_price','list_price','percent_bronze','percent_silver','percent_gold')
    def _compute_price(self): 
        for product in self.sudo():
            
            tax_inc = False
            
            for tax in product.taxes_id:
                if tax.price_include:
                    tax_inc = True
            
            if product.list_price_base == 'standard_price':
                price = product.standard_price
            else:
                price = product.list_price
                if tax_inc:
                    taxes = product.taxes_id.compute_all(product.list_price, 1)
                    price = taxes['total']
                                

            
            product.list_price_bronze =  price  * (1 + product.percent_bronze)            
            product.list_price_silver =  price  * (1 + product.percent_silver)
            product.list_price_gold  =   price  * (1 + product.percent_gold)
            
            if tax_inc: 
                taxes = product.taxes_id.compute_all( product.list_price_bronze, 1, force_excluded=True)
                product.list_price_bronze =  taxes['total_included']
                taxes = product.taxes_id.compute_all( product.list_price_silver, 1, force_excluded=True)
                product.list_price_silver =  taxes['total_included']            
                taxes = product.taxes_id.compute_all( product.list_price_gold, 1, force_excluded=True)
                product.list_price_gold =  taxes['total_included']            
                
           
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
