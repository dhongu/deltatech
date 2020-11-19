# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAlternativeLink(WebsiteSale):
    @http.route(["/<category>"], type="http", auth="public", website=True, sitemap=False)
    def shop_category(self, page=0, category=None, search="", ppg=False, **post):
        if category:
            Category = request.env["product.public.category"]
            category = Category.search([("alternative_link", "=", category)], limit=1)
            if category:
                res = self.shop(page=page, category=category.id, search=search, ppg=ppg, **post)
                return res
        raise request.not_found()
