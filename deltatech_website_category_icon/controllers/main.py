# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class CategoryIconGrid(http.Controller):
    @http.route("/website/snippet/category_icon_grid", type="jsonrpc", auth="public", website=True, readonly=True)
    def category_icon_grid(self, category_ids=None, limit=12):
        """Items of the snippet Category Icon Grid, rendered for the current website."""
        categories = request.env["product.public.category"]._get_icon_grid_categories(
            request.website, category_ids, limit
        )
        if not categories:
            return ""
        values = {"categories": categories, "category_url": WebsiteSale._get_shop_path}
        return str(
            request.env["ir.ui.view"]._render_template(
                "deltatech_website_category_icon.s_category_icon_grid_items", values
            )
        )
