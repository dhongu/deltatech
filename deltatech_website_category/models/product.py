# coding: utf-8
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C)2010-  OpenERP SA (<http://openerp.com>). All Rights Reserved
#    App Author: Vauxoo
#
#    Developed by Oscar Alcala
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
from datetime import datetime
import time
from openerp import SUPERUSER_ID

import time

class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    @api.returns('self',
        upgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else self.browse(value),
        downgrade=lambda self, value, args, offset=0, limit=None, order=None, count=False: value if count else value.ids)
    def search(self, cr, user, args, offset=0, limit=None, order=None, context=None, count=False):
        if context and context.get('website_order_by',False):
            order = context['website_order_by']
        res =  super(ProductTemplate,self).search( cr,  user, args, offset, limit, order, context, count)
        return res
    
    

class ProductCategory(models.Model):
    _inherit = 'product.public.category'

    product_ids = fields.Many2many('product.template', relation='product_public_category_product_template_rel', column1='product_public_category_id', column2='product_template_id')
    total_tree_products = fields.Integer("Total Subcategory Prods",  compute="_get_product_count", store=True)


    @api.multi
    def _get_products(self):
        product_obj = self.env["product.template"]
        for record in self:
            #print "determinare produse care sunt intr-o categorie"
            start_time = time.time()

            product_ids = []
            product_published = product_obj.search( [("website_published", "=", True)])

            for product in product_published:
                if record in product.public_categ_ids:
                    product_ids.append(product.id)
            record.product_ids = product_ids
            #print("--- %s seconds ---" % (time.time() - start_time))


    @api.multi
    @api.depends('product_ids')
    def _get_product_count(self):
        prod_obj = self.env["product.template"]
        for rec in self:
            if not isinstance(rec.id, models.NewId):
                counts = prod_obj.search_count( [('public_categ_ids', 'child_of', rec.id),
                                                   ('website_published', '=', True)])
                rec.total_tree_products = counts
