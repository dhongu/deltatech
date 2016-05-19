# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################


import openerp
from openerp import http
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale
from openerp.addons.website_sale.controllers.main import QueryURL
import time
    
class WebsiteSale(website_sale):
    @http.route(
        [
         '/shop',
         '/shop/page/<int:page>',
         '/shop/category/<model("product.public.category"):category>',
         '/shop/category/<model("product.public.category"):category>/page/<int:page>'],
        type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', order_by='', **post):
        
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
        
         
        start_time = time.time()
        
         
        parent_category_ids = []
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id

        context = request.context
        if context is None:
            context = {}

        order_by = order_by or request.session.get('website_order_by', False)
        
        #print "Order ", order_by
        
         
        context['website_order_by'] = order_by
        request.session['website_order_by'] = order_by
        
         
        request.context =  context   
        
        response = super(WebsiteSale, self).shop(
            page=page, category=category, search=search, **post)

 
        
        response.qcontext['parent_category_ids'] = parent_category_ids
        
        response.qcontext['order_by'] = order_by
       
 
        #print "Stop selectie date"
        #print("--- %s seconds ---" % (time.time() - start_time))
        
        return response


    def _get_mandatory_billing_fields(self):   
        mandatory_billing_fields = ["name", "phone"]     
        return mandatory_billing_fields
 
    def _get_mandatory_shipping_fields(self):
        mandatory_shipping_fields = ["name", "phone", "street", "city"]
        return self.mandatory_shipping_fields

#openerp.addons.website_sale.controllers.main.website_sale = WebsiteSale