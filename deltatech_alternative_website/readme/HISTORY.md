## 19.0.1.0.9 (2026-09-26)

- Roadmap: replaced the manual `CREATE INDEX ... gin_trgm_ops` SQL with the
  indexes Odoo 19 already maintains (`variants_default_code` and
  `default_code` in `website_sale`, `product.alternative.name` in
  `deltatech_alternative`). Documentation only, no code change.

## 19.0.1.0.8 (2026-07-27)

- Fix: the website search (autocomplete and shop) raised
  `ValueError: list.remove(x): x not in list` when the search bar snippet
  had the description display turned off. `website_sale` only adds
  `description` / `description_sale` to `search_fields` when
  `displayDescription` is set, while this module removed them
  unconditionally. They are now removed only when present.
- Added tests for `_search_get_detail` with the description display on and
  off.
