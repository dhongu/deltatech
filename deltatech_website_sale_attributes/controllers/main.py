from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        # Store used domain in context to be reused after
        domain = super()._get_search_domain(
            search, category, attrib_values, search_in_description=search_in_description
        )
        request.update_context(shop_search_domain=domain)
        return domain

    @http.route()
    def shop(self, page=0, category=None, search="", ppg=False, **post):
        response = super().shop(page, category, search, ppg, **post)

        # Normalize values coming from super's rendering context
        qctx = response.qcontext
        q_category = qctx.get("category")
        q_search = qctx.get("search") or search or post.get("search")
        attrib_values = qctx.get("attrib_values")

        if q_category or q_search:
            # Try to reuse domain computed during super().shop, else recompute
            domain = request.env.context.get("shop_search_domain")
            if domain is None:
                domain = self._get_search_domain(q_search or "", q_category, attrib_values)

            products = request.env["product.template"].with_context(prefetch_fields=False).search(domain)

            ptal_domain = [("product_tmpl_id", "in", products.ids)]
            attribute_lines = request.env["product.template.attribute.line"].search(ptal_domain)

            value_ids = attribute_lines.mapped("value_ids")

            if q_category:
                # hide other categories; keep current category context
                categories = q_category
                response.qcontext.update(categories=categories)
        else:
            domain = [("visibility", "=", "visible")]
            value_ids = request.env["product.attribute.value"].search(domain)

        response.qcontext.update(value_ids=value_ids)

        return response
