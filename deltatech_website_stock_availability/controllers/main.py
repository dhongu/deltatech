from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        response = super(WebsiteSaleAttribute, self).shop(page, category, search, ppg, **post)
        availability_all = request.httprequest.args.get("availability_all", True)
        availability_in_stock = request.httprequest.args.get("availability_in_stock", False)
        response.qcontext.update(availability_all=availability_all, availability_in_stock=availability_in_stock)

        return response
