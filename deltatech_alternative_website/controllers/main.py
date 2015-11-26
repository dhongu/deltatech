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



import openerp
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main

"""
class website_sale(openerp.addons.website_sale.controllers.main.website_sale):


    def _get_search_domain(self, search, category, attrib_values):
        domain = super(website_sale,self)._get_search_domain(search, category, attrib_values)
        print "cautare dupa:", domain
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        alternative_ids = []
        product_ids = []
        if search:
            alt_domain = []
            for srch in search.split(" "):
                alt_domain += [ ('name', '=ilike', srch)]
            alternative_ids =  pool['product.alternative'].search(cr,uid,  alt_domain, limit=10 ) 
            for alternative in pool['product.alternative'].browse(cr,uid, alternative_ids):
                product_ids += alternative.product_tmpl_id.product_variant_ids.ids
        if product_ids:
            domain = [('id','in', str(product_ids))]
            print "cautare dupa:", domain
        return domain
"""

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
