## 20.0.1.0.10 (2026-10-16)

Migration to 20.0:

- The product page script patches the `ProductPage` interaction (`website_sale.product_page`)
  and waits for the asynchronous core `_onChangeCombination`; the selected variant is read
  from the add to cart button, as the `.product_id` input no longer exists.
- The lead time data is added when the `website_sale_product_page` context is set (replaces
  `website_sale_stock_get_quantity`).
- "Customer Safety Lead Time" is shown below "Customer Lead Time" in the Sales section of the
  product form; "Hide Out-of-Stock Message" stays in the eCommerce inventory group.
- The optional "Delivery Lead Time" checkout summary view targets the product name cell (the
  previous xpath matched nothing and the view could not be activated).
- "Delivery in N weeks" for a customer lead time over 7 days showed `NaN`; it now uses the
  customer lead time.

# 19.0.1.0.10

- Own module icon, instead of the generic gears it had.

# History

## 19.0.1.0.9 (2026-07-30)

- Fixed `?ppg=` silently filtering the shop by price. The `shop()` override
  declared `(page, category, search, ppg)` and forwarded those positionally,
  but core's fourth slot is `min_price`, so `?ppg=40` reached it as
  `min_price=40` and dropped every cheaper product from the listing while the
  page size stayed at its default. On 19.0 `ppg` is not a core parameter at
  all, yet declaring it here still captured it and pushed it into
  `min_price`. The override now forwards by keyword only.
