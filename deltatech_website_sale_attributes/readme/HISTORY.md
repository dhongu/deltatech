## 19.0.1.0.6 (2026-11-03)

- Description rewritten after the code: the module adds a *Visibility* (Visible / Hidden) field on
  attribute values and leaves the hidden values out on the product page; it does not override the
  shop templates and does not filter the values by the products listed.
- Added a Limitations section: the shop sidebar filters still show the hidden values.
- Summary and Apps banner aligned with the description.

## 19.0.1.0.5 (2026-10-09)

- Apps Store banner (banner.json).

# 19.0.1.0.4

- Own module icon, instead of the generic gears it had.

# History

## 19.0.1.0.3 (2026-07-30)

- Fixed `?ppg=` silently filtering the shop by price. The `shop()` override
  declared `(page, category, search, ppg)` and forwarded those positionally,
  but core's fourth slot is `min_price`, so `?ppg=40` reached it as
  `min_price=40` and dropped every cheaper product from the listing while the
  page size stayed at its default. On 19.0 `ppg` is not a core parameter at
  all, yet declaring it here still captured it and pushed it into
  `min_price`. The override now forwards by keyword only.
