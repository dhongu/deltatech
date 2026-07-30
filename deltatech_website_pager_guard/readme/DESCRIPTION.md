Makes the shop return **404** for listing pages that do not exist.

Odoo's `pager()` helper clamps an out-of-range page number to the last real
page rather than refusing it. `/shop/page/999999` therefore answers `200` with
the content of the last page — and a crawler reads that as confirmation that
the page exists, follows the pattern upwards and never stops.

On a production site this produced 2.386 requests per day against a single
`/shop/category/…/page/3467514` URL, each one paying for a full product search
and QWeb render before serving duplicate content.

This module compares the requested page against the pager's own `page_count`
and raises `NotFound` when it is higher. `/shop` itself and the last real page
are unaffected, so search engines get a clean signal that the URL space is
finite.

Deliberately **no hardcoded page ceiling**: a real catalogue was measured at
2.578 shop pages, so even a limit that looks generous would refuse most of the
listing. The page count is only known once the products are counted, which is
why the check runs after `super()`. That still avoids the expensive part —
`request.render` is lazy in Odoo, so raising there means the QWeb template is
never rendered.
