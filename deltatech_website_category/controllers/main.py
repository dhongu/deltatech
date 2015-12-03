# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


import openerp
from openerp import http
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL
#import time
    
class WebsiteSale(website_sale):
    @http.route(
        [
         '/shop',
         '/shop/page/<int:page>',
         '/shop/category/<model("product.public.category"):category>',
         '/shop/category/<model("product.public.category"):category>/page/<int:page>'],
        type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', **post):
        parent_category_ids = []
        if category:
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id
        #print "Start selectie date"
        #start_time = time.time()
        response = super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)

        has_products = lambda categ: self._child_has_products(categ)    # noqua
        
        response.qcontext['parent_category_ids'] = parent_category_ids
        response.qcontext['_has_products'] = has_products
        #print "Stop selectie date"
        #print("--- %s seconds ---" % (time.time() - start_time))
        return response

    def _child_has_products(self, category):
        if category.child_id:
            return any(self._child_has_products(child)
                       for child in category.child_id)
        elif category.product_ids:
            return True
        else:
            return False

#openerp.addons.website_sale.controllers.main.website_sale = WebsiteSale