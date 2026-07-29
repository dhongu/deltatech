# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.const import SHOP_PATH


class WebsiteSaleCategory(http.Controller):
    @http.route(
        f"{SHOP_PATH}/category_children/<int:category_id>",
        type="http",
        auth="public",
        website=True,
        sitemap=False,
        readonly=True,
    )
    def shop_category_children(self, category_id, active_category=None, offcanvas=None, **kwargs):
        """Return the direct children of one collapsed sidebar branch.

        The listing page renders only the open branch (see
        ``lazy_collapse_categories_recursive``); the rest is fetched here when
        the visitor expands a node.

        ``active_category`` is the category the page itself is showing. It only
        drives the ``isOpen`` / underline state of the returned nodes, so an
        unknown or inaccessible id is simply ignored rather than refused.

        Any other query argument is the listing page's own filter state
        (``order``, ``min_price``, ``attribute_value``, ...) and is fed back
        into ``QueryURL`` so the fetched links carry the same state as the ones
        rendered server-side.

        The response deliberately carries no ``qcontext``, so
        ``_register_website_track`` finds no template and skips visitor
        tracking — expanding a branch is navigation inside a page already
        counted, and the ``website_visitor`` upsert is a known contention point
        under crawler load.
        """
        Category = request.env["product.public.category"]

        parent = Category.browse(category_id).exists()
        if not parent or not parent.can_access_from_current_website():
            raise NotFound()

        children = parent.child_id.filtered(lambda c: c.can_access_from_current_website())
        # Mirror the sidebar: portal users only ever see categories leading to a
        # published product, so a fetched branch must not reveal more than the
        # server-rendered one would.
        if not request.env.user._is_internal():
            children = children.filtered("has_published_products")
        if not children:
            return request.make_response("", headers=[("Content-Type", "text/html")])

        category = Category
        if active_category:
            try:
                candidate = Category.browse(int(active_category)).exists()
            except ValueError:
                candidate = Category
            if candidate and candidate.can_access_from_current_website():
                category = candidate

        # Rebuild the filter state from the raw args rather than from **kwargs:
        # a repeated parameter (`attribute_value`) collapses to its last value
        # in kwargs, which would silently drop attribute filters from the
        # fetched links.
        args = request.httprequest.args
        query = {}
        for key in args.keys():
            if key in ("category", "active_category", "offcanvas"):
                continue
            values = args.getlist(key)
            query[key] = values if len(values) > 1 else values[0]
        keep = QueryURL(SHOP_PATH, **query)

        content = request.env["ir.ui.view"]._render_template(
            "deltatech_website_category.lazy_categories_children",
            {
                "children": children,
                "category": category,
                "search": "",
                "search_categories_ids": [],
                "keep": keep,
                # 19.0 builds category links from `shop_path`; without it in the
                # render values `categorie_link` raises.
                "shop_path": SHOP_PATH,
                "isOffcanvas": offcanvas == "1",
                "parentCategoryId": parent.id,
            },
        )
        return request.make_response(content, headers=[("Content-Type", "text/html")])
