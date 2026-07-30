# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from werkzeug.exceptions import NotFound

from odoo.http import route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSalePagerGuard(WebsiteSale):
    """Refuse shop listing pages that do not exist.

    ``portal.controllers.portal.pager`` clamps an out-of-range page number to
    the last real page instead of refusing it, so ``/shop/page/999999`` answers
    200 with the content of the last page. Crawlers read that as "the page
    exists", follow the pattern upwards and never terminate: production logs
    showed 2.386 hits/day on a single ``/page/3467514`` URL, each paying for a
    full product search and QWeb render.
    """

    @route(
        [
            "/shop",
            "/shop/page/<int:page>",
            '/shop/category/<model("product.public.category"):category>',
            '/shop/category/<model("product.public.category"):category>/page/<int:page>',
        ],
        type="http",
        auth="public",
        website=True,
        sitemap=WebsiteSale.sitemap_shop,
    )
    def shop(self, page=0, category=None, search="", min_price=0.0, max_price=0.0, ppg=False, **post):
        response = super().shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post,
        )

        # ``page`` is 0 on ``/shop`` itself, which always exists. Other modules
        # may answer with a template that has no pager (for instance a category
        # selection screen), hence the ``get``.
        #
        # No cheaper pre-search shortcut is possible here: the page count is
        # only known once the products are counted, and any hardcoded ceiling
        # would refuse real pages. A live catalogue was measured at 2.578 shop
        # pages, so even a generous-looking limit like 500 would have broken
        # four fifths of the listing. Refusing after ``super()`` still skips
        # the expensive part — ``request.render`` is lazy, so raising here
        # means the QWeb template is never rendered.
        pager = getattr(response, "qcontext", {}).get("pager")
        if page > 1 and pager and page > pager["page_count"]:
            raise NotFound()

        return response
