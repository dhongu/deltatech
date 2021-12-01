# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAlternativeLink(WebsiteSale):
    @http.route(["/<string:alternative_link>"], type="http", auth="public", website=True, sitemap=False)
    def shop_alternative_link(self, alternative_link=None, **post):
        if alternative_link:
            Category = request.env["product.public.category"]
            category = Category.search([("alternative_link", "=", alternative_link)], limit=1)
            if category:
                res = self.shop(category=category.id, **post)
                return res

            Product = request.env["product.template"]
            product = Product.search([("alternative_link", "=", alternative_link)], limit=1)
            if product:
                res = self.product(product=product, **post)
                return res
        raise request.not_found()
