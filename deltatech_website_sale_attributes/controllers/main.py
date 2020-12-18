from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        # Store used domain in context to be reused after
        domain = super()._get_search_domain(
            search, category, attrib_values, search_in_description=search_in_description
        )
        new_context = dict(request.env.context, shop_search_domain=domain)
        request.context = new_context
        return domain

    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        response = super(WebsiteSaleAttribute, self).shop(page, category, search, ppg, **post)

        if category and search:
            # attrib_values = response.qcontext.get("attrib_values")
            category = response.qcontext.get("category")
            # domain = self._get_search_domain(search, category, attrib_values)
            domain = request.env.context.get("shop_search_domain", [])

            # value_ids = request.env["product.attribute.value"]
            # products = response.qcontext.get("products")
            products = request.env["product.template"].with_context(prefetch_fields=False).search(domain)

            domain = [("product_tmpl_id", "in", products.ids)]
            attribute_lines = request.env["product.template.attribute.line"].search(domain)

            value_ids = attribute_lines.mapped("value_ids")
            # domain = [("pav_attribute_line_ids", "in", attribute_lines.ids)]
            # value_ids = request.env["product.attribute.value"].search(domain)

            if category:
                # se ascund restul de caterorii
                # categories = request.env['product.public.category'].search([('id','child_of',category.id)])
                categories = category
                response.qcontext.update(categories=categories)
        else:
            value_ids = request.env["product.attribute.value"].search([])

        response.qcontext.update(value_ids=value_ids)

        return response
