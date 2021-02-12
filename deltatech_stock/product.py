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


from openerp.osv import fields
from openerp.osv import osv

import openerp.pooler
import time
from openerp.tools.translate import _

class product_template(osv.osv):
    _inherit = "product.template"
 
    def get_history_price(self, cr, uid, product_tmpl, company_id, date=None, context=None): 
        res = super(product_template,self).get_history_price(cr, uid, product_tmpl, company_id, date, context)
        if res == 0.0 :
            prod =  self.browse(cr, uid, product_tmpl, context=context)
            res = prod.standard_price
        return res   


    

class product_product(osv.osv):
    _inherit = 'product.product'

    def create(self, cr, uid, vals, context={}):
        default_code = vals.get('default_code', '') 
        if (default_code == '' or default_code == 'auto' ) and vals.get('categ_id', False) :
            category = self.pool.get('product.category').browse( cr, uid,  vals['categ_id'])
            if category.sequence_id:
                vals['default_code'] =  self.pool.get('ir.sequence').next_by_id(cr, uid,  category.sequence_id.id  )
            
        res = super(product_product, self).create(cr, uid,  vals, context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('default_code') == 'auto':
            for product in self.browse(cr, uid, ids, context=context):
                category = product.categ_id
                temp_vals = {}
                if category.sequence_id:
                    temp_vals['default_code'] =  self.pool.get('ir.sequence').next_by_id(cr, uid,  category.sequence_id.id  )
                    super(product_product, self).write(cr, uid, [product.id], temp_vals, context=context) 
                    del vals['default_code']
        res = super(product_product, self).write(cr, uid, ids, vals, context=context)            
        return res
        





class product_category(osv.osv):
    _inherit = 'product.category'
    _columns = {
        'sequence_id': fields.many2one('ir.sequence', 'Code Sequence', required=False),
    }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
