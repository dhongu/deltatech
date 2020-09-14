# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.osv import expression


class WebsiteSnipped(http.Controller):
    @http.route(["/snipped/render_category_list"], type="json", auth="public", website=True)
    def render_category_list(self, template, domain, limit=None):
        dom = []
        if domain:
            dom = expression.AND([dom, domain])
        categories = request.env["product.public.category"].search(dom, limit=limit)
        return request.website.viewref(template).render({"categories": categories})
