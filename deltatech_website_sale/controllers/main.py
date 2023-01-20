# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale as Base


class WebsiteSale(Base):
    @route()
    def address(self, **kw):
        result = super(WebsiteSale, self).address(**kw)
        result.qcontext["country"] = result.qcontext.get("country") or request.website.company_id.country_id
        return result

    @http.route(
        [
            "/shop",
            "/shop/page/<int:page>",
            """/shop/category/<model("product.public.category"):category>""",
            """/shop/category/<model("product.public.category"):category>/page/<int:page>""",
        ],
        type="http",
        auth="public",
        website=True,
    )
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        if isinstance(category, str):
            category = False
        return super(WebsiteSale, self).shop(page=page, category=category, search=search, ppg=ppg, **post)
