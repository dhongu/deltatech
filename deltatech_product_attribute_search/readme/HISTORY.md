# 19.0.1.0.0 (2026-09-23)

- First version. `product.product` searches now also look at the values of the
  variant's attributes, both on the product field of an order line (`name_search`)
  and wherever `display_name` is searched — search views, `search()` domains,
  import matching (`_search_display_name`).
- The query is split on whitespace and every word has to match the template name,
  the internal reference or one of the attribute values, so a query can mix them
  (`apples gala 80`). Past five words the input is treated as a pasted line and
  left to standard Odoo.
- Standard Odoo answers first and the attribute lookup only fills what is left of
  the page, so the module costs nothing on searches that already returned results.
- A query of a single word adds **only** the attribute lookup, since standard Odoo
  has already covered the name and the reference. That keeps it on indexes all the
  way: measured on 20.000 variants, 0,6 ms for the lookup and 9 ms for the whole
  `name_search`, against 17 ms for a standard search that finds its answer. Several
  words cost one pass over the variants (34 ms on the same data) — unavoidable,
  because `ilike` on a translated name cannot use an index, and standard Odoo pays
  the same price for its own name lookup.
- The values of attribute lines carrying a single value are searched too, although
  Odoo leaves them out of the variant's name. A product whose only variety is
  `Idared` is still an Idared, and a search finding it on one template but not on
  another would look like missing data.
- New `search_ok` flag on `product.attribute` (default on), to keep an attribute
  with generic values out of the search.
