## 18.0.1.1.0 (2026-07-29)

- The shop sidebar now renders only the open branch of the category tree.
  Collapsed branches ship an empty list and are filled from
  `/shop/category_children/<id>` when the visitor expands them, which is the
  first moment their content becomes visible.

  On a catalog with 1222 public categories the listing page went from 0.82s to
  0.23s (-72%) and from 2.22 MB to 1.20 MB of HTML, with the same 20 products
  displayed. The tree was the dominant cost of the page: a product detail page
  on the same site renders in 0.15s with a comparable number of queries.

  Nothing changes visually — the collapsed markup was never on screen. While a
  search is active the (already filtered, already small) tree stays fully
  rendered, so search behaviour is untouched.
