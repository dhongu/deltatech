from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    @http.route(["/shop/cart"], type="http", auth="public", website=True)
    def cart(self, access_token=None, revive="", **post):
        if revive == "reopen":
            request.website.reopen_last_order()
        return super(WebsiteSale, self).cart(access_token=access_token, revive=revive, **post)
