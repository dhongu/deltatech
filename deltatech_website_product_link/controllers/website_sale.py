# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import http
from odoo.http import request

from odoo.addons.web.controllers.main import Binary
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAlternativeLink(WebsiteSale):
    @http.route(["/<category>"], type="http", auth="public", website=True, sitemap=False)
    def shop_category(self, page=0, category=None, search="", ppg=False, **post):
        if category:
            Category = request.env["product.public.category"]
            category = Category.search([("alternative_link", "=", category)], limit=1)
            if category:
                return self.shop(page=page, category=category.id, search=search, ppg=ppg, **post)
        raise request.not_found()


class BinaryAlternativeLink(Binary):
    @http.route(
        ["/continut/produse/<int:legacy_id>/<int:height>/<filename>"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def old_image_link(self, legacy_id, height, filename, **post):
        Product = request.env["product.template"]
        product = Product.search([("legacy_id", "=", legacy_id)])
        if product:
            return self._content_image(
                model="product.template", id=product.id, field="image_1920", height=height, filename=filename
            )
