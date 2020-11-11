from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        response = super(WebsiteSaleAttribute, self).shop(page, category, search, ppg, **post)

        attrib_values = response.qcontext.get("attrib_values")
        category = response.qcontext.get("category")
        domain = self._get_search_domain(search, category, attrib_values)

        value_ids = request.env["product.attribute.value"]
        # products = response.qcontext.get("products")
        products = request.env["product.template"].search(domain)

        domain = [("product_tmpl_id", "in", products.ids)]
        attribute_lines = request.env["product.template.attribute.line"].search(domain)

        domain = [("pav_attribute_line_ids", "in", attribute_lines.ids)]
        value_ids = request.env["product.attribute.value"].search(domain)
        # for line in attribute_lines:
        #     value_ids |= line.value_ids
        if category:
            # se ascund restul de caterorii
            # categories = request.env['product.public.category'].search([('id','child_of',category.id)])
            categories = category
            response.qcontext.update(categories=categories)

        response.qcontext.update(value_ids=value_ids)

        return response
