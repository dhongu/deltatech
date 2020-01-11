# Copyright 2015, 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.http import request, route
from odoo.addons.website_sale.controllers.main import WebsiteSale as Base
from odoo import fields, http, tools, _

class WebsiteSale(Base):
    @route()
    def address(self, **kw):
        result = super(WebsiteSale, self).address(**kw)
        result.qcontext["country"] = (
            result.qcontext.get("country") or
            request.website.company_id.country_id)
        return result





    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>''',
        '''/shop/category/<model("product.public.category", "[('website_id', 'in', (False, current_website_id))]"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if isinstance(category, str):
            category = False
        return super(WebsiteSale, self).shop(page=page, category=category, search=search, ppg=ppg, **post)


    """
    de modificat din t-att-action="keep('/shop'+ ('/category/'+slug(category)) if category else None, search=0)"
    in t-att-action="keep('/shop')"
    
        <template id="search" name="Search Box">
        <form t-att-action="keep('/shop'+ ('/category/'+slug(category)) if category else None, search=0)" method="get" t-att-class="_classes">
            <t t-if="attrib_values">
                <t t-foreach="attrib_values" t-as="a">
                    <input type="hidden" name="attrib" t-att-value="'%s-%s' % (a[0], a[1])" />
                </t>
            </t>
            <t t-call="website.website_search_box" />
        </form>
    </template>
    
    """