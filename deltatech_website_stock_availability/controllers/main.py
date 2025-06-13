from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        response = super().shop(page, category, search, ppg, **post)
        availability_all = request.httprequest.args.get("availability_all", True)
        availability_in_stock = request.httprequest.args.get("availability_in_stock", False)
        availability_vendor = request.httprequest.args.get("availability_vendor", False)
        response.qcontext.update(
            availability_all=availability_all,
            availability_in_stock=availability_in_stock,
            availability_vendor=availability_vendor,
        )

        return response
