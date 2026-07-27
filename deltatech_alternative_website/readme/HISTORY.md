## 18.0.1.1.2 (2026-07-27)

- Fix: the website search (autocomplete and shop) raised
  `ValueError: list.remove(x): x not in list` when the search bar snippet
  had the description display turned off. `website_sale` only adds
  `description` / `description_sale` to `search_fields` when
  `displayDescription` is set, while this module removed them
  unconditionally. They are now removed only when present.
- Added tests for `_search_get_detail` with the description display on and
  off.
