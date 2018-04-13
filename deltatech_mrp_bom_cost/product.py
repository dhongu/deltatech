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
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from openerp.osv.fields import related

from openerp.addons.product import _common

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    standard_price = fields.Float(track_visibility='always')

    @api.multi
    def write(self, vals):
        res = super(ProductTemplate,self).write(vals)
        for template in self:
            if 'standard_price' in vals and template.product_variant_count == 1:
                product = template.product_variant_ids[0]
                if vals['standard_price'] <> product.standard_price:
                    product.write({'standard_price':vals['standard_price']})          
        return res


    
 
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    bom_price = fields.Float(digits= dp.get_precision('Account'), string='BOM Price', track_visibility='always')
    standard_price = fields.Float(track_visibility='always')
    is_simple_product = fields.Boolean(string="Base product")
    
    

    @api.one
    @api.onchange('product_attributes','bom_ids')
    def _calculate_bom_price(self ):
        bom_id = self.env['mrp.bom']._bom_find( product_id = self.id)
        if bom_id:
            bom = self.env['mrp.bom'].browse(bom_id)
            # trebuie facut update si la lista de atribute daca aceasta lipseste
            if  not self.product_attributes and self.attribute_value_ids:
                self.product_attributes = self._get_product_attributes_values_dict() 
            
            self.bom_price = bom.with_context(production=self).calculate_price
            self.standard_price = self.bom_price


        else:
            self.bom_price = self.standard_price or self.product_tmpl_id.standard_price
        
        #print self.name, self.bom_price


    @api.multi
    def update_bom_price(self):
        for product in self:
            product._calculate_bom_price()

    @api.multi
    def button_update_bom_price(self):
        for product in self:
            bom_id = self.env['mrp.bom']._bom_find( product_id = product.id)
            if bom_id:
                bom = self.env['mrp.bom'].browse(bom_id)
                for line in bom.bom_line_ids:  
                    if line.product_id:
                        line.product_id.update_bom_price()                
                # trebuie facut update si la lista de atribute daca aceasta lipseste
                if  not product.product_attributes and product.attribute_value_ids:
                    product.product_attributes = product._get_product_attributes_values_dict() 
                
                product.bom_price = bom.with_context(production=product).calculate_price
                 
            else:
                product.bom_price = product.standard_price or product.product_tmpl_id.standard_price
                
            
    
    #am redefini metoda pentru a afisa toate bom-urile
    def action_view_bom(self, cr, uid, ids, context=None):
        tmpl_obj = self.pool.get("product.template")
        products = set()
        for product in self.browse(cr, uid, ids, context=context):
            products.add(product.product_tmpl_id.id)
        result = tmpl_obj._get_act_window_dict(cr, uid, 'mrp.product_open_bom', context=context)
        # bom specific to this variant or global to template
        domain = [
            '|',
                ('product_id', 'in', ids),
                '&',
                    #('product_id', '=', False),
                    ('product_tmpl_id', 'in', list(products)),
        ]
        result['context'] = "{'default_product_id': active_id, 'search_default_product_id': active_id, 'default_product_tmpl_id': %s}" % (len(products) and products.pop() or 'False')
        result['domain'] = str(domain)
        return result


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: