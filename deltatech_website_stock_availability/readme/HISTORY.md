# 19.0.1.0.13

- The stock badge on the product page ("4 Units in stock", shown under the
  availability threshold) gets a style picked from the website builder, in the
  "Product Page" options, "Stock Badge": the standard pill, text with a dot,
  theme colors, outline, a level bar filled up to the threshold, or the status
  only ("Limited stock", without the quantity). The new styles take their
  colors from the website theme, so they stay readable on dark themes.

# 19.0.1.0.12

- The stock status on the shop product card is configured from the website
  builder, in the "Products Design" panel: shown as text, LED or LED with text,
  placed above the price, on the image or next to the price, with orange, gray
  or red for products not in stock. Websites that had the "Product Available"
  card badge active keep it, as text above the price.

# 19.0.1.0.11

- The vendor stock and lead time on the product page now come from the supplier
  that really applies to the selected variant: suppliers of another variant, of
  another company, of an archived vendor or with an expired offer are skipped,
  and a current offer wins over a future one.
- The cart delivery badges now use the stock of the website warehouse, expressed
  in the unit of the cart line (a line of one dozen with six units in stock is no
  longer shown as "Immediate delivery").

# 19.0.1.0.10

- Own module icon, instead of the generic gears it had.

# History

## 19.0.1.0.14 (2026-10-22)

- Listed on Odoo Apps as *Website Stock Availability* (was *eCommerce Stock Availability*). The technical name `deltatech_website_stock_availability` does not change.

## 19.0.1.0.9 (2026-07-30)

- Fixed `?ppg=` silently filtering the shop by price. The `shop()` override
  declared `(page, category, search, ppg)` and forwarded those positionally,
  but core's fourth slot is `min_price`, so `?ppg=40` reached it as
  `min_price=40` and dropped every cheaper product from the listing while the
  page size stayed at its default. On 19.0 `ppg` is not a core parameter at
  all, yet declaring it here still captured it and pushed it into
  `min_price`. The override now forwards by keyword only.
