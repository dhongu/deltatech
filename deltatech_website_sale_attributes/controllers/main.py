from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        response = super(WebsiteSaleAttribute, self).shop(page, category, search, ppg, **post)

        value_ids = request.env["product.attribute.value"]
        products = response.qcontext.get("products")

        domain = [("product_tmpl_id", "in", products.ids)]
        attribute_lines = request.env["product.template.attribute.line"].search(domain)

        for line in attribute_lines:
            value_ids |= line.value_ids

        response.qcontext.update(value_ids=value_ids)

        return response
