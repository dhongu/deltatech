# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Terrabit Solutions All Rights Reserved
#                    Dan Stoica <danila(@)terrabit(.)ro
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

class CalculateBOMPrices(models.TransientModel):
    _name='calculate_bom_prices'

    @api.multi
    def action_calculate_boms(self):
        print 'Update BOM prices wizard started:'
        print 'Calculating BOM prices for simple products...'
        products = self.env['product.product'].search([('is_simple_product', '=', True)])
        for product in products:
            product.bom_price = product.standard_price

        print 'Calculating bom prices for products'
        for i in range(4):
            print 'Iteration # '+str(i)+':'
            products = self.env['product.product'].search([('active','=',True)])
            for product in products:
                if product.product_tmpl_id.bom_count>0:
                    product_initial_price = product.bom_price
                    product._calculate_bom_price()
                    if str(product_initial_price) != str(product.bom_price):
                        print product.name+':'+str(product_initial_price)+'->'+str(product.bom_price)
