## 19.0.1.1.1 (2026-07-30)

- `/shop/category_children/<id>` no longer echoes unknown query parameters
  back into the links of the fetched branch. It copied every raw argument
  into `QueryURL`, so anything a visitor appended was woven into every link
  on the page — unlike core, which keeps only its own filter parameters in
  `_shop_get_query_url_kwargs`. Crawlers that fail to decode HTML entities
  request `&amp;order=` literally, which Odoo parses as a parameter named
  `amp;order`; echoing it back would have published a fresh set of URLs on
  every pass.

## 19.0.1.1.0 (2026-07-29)

- First 19.0 release of this module. It carries over the 18.0 features that core
  still does not provide (archivable public categories, `website_url`) plus the
  lazy category tree below.

  `website_footer_description` is **not** carried over: 19.0 core ships
  `product.public.category.website_footer` and renders it on the listing page,
  so the module's own field would only duplicate it. A database moving from 18.0
  to 19.0 needs its `website_footer_description` values copied into
  `website_footer`.

- The shop sidebar renders only the open branch of the category tree. Collapsed
  branches ship an empty list and are filled from
  `/shop/category_children/<id>` when the visitor expands them, which is the
  first moment their content becomes visible.

  Measured on the 18.0 equivalent against a 1222-category catalog: the listing
  page went from 0.82s to 0.23s (-72%) and from 2.22 MB to 1.20 MB of HTML, with
  the same 20 products displayed.

  Nothing changes visually — the collapsed markup was never on screen. While a
  search is active the (already filtered, already small) tree stays fully
  rendered, so search behaviour is untouched.
