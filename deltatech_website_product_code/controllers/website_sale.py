# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAlternativeLink(WebsiteSale):
    @http.route(["/shop/product-code/<code>"], type="http", auth="public", website=True, sitemap=False)
    def product_by_code(self, code="", **kwargs):
        product = request.env["product.template"].search([("default_code", "=", code)], limit=1)
        if not product:
            raise request.not_found()
        return self.product(product, **kwargs)
