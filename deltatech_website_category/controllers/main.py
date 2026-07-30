# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from odoo.addons.website.controllers.main import QueryURL


class WebsiteSaleCategory(http.Controller):
    # Query parameters carried into the links of a fetched branch. Mirrors what
    # ``WebsiteSale._shop_get_query_url_kwargs`` keeps, minus ``category``,
    # which the templates supply themselves.
    _KEPT_QUERY_PARAMS = (
        "search",
        "order",
        "min_price",
        "max_price",
        "tags",
        "attribute_value",
    )

    @http.route(
        "/shop/category_children/<int:category_id>",
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
        #
        # Only the parameters core itself carries over are copied — see
        # ``WebsiteSale._shop_get_query_url_kwargs``. Anything else a visitor
        # appends to the URL is dropped instead of being woven into every link
        # on the page. ``category`` is absent on purpose: the templates pass
        # ``category=0`` to keep it out of these URLs.
        args = request.httprequest.args
        query = {}
        for key in self._KEPT_QUERY_PARAMS:
            values = args.getlist(key)
            if values:
                query[key] = values if len(values) > 1 else values[0]
        keep = QueryURL("/shop", **query)

        content = request.env["ir.ui.view"]._render_template(
            "deltatech_website_category.lazy_categories_children",
            {
                "children": children,
                "category": category,
                "search": "",
                "search_categories_ids": [],
                "keep": keep,
                "isOffcanvas": request.params.get("offcanvas") == "1",
                "parentCategoryId": parent.id,
            },
        )
        return request.make_response(content, headers=[("Content-Type", "text/html")])
