# History

## 19.0.1.0.3 (2026-07-30)

- Fixed `?ppg=` silently filtering the shop by price. The `shop()` override
  declared `(page, category, search, ppg)` and forwarded those positionally,
  but core's fourth slot is `min_price`, so `?ppg=40` reached it as
  `min_price=40` and dropped every cheaper product from the listing while the
  page size stayed at its default. On 19.0 `ppg` is not a core parameter at
  all, yet declaring it here still captured it and pushed it into
  `min_price`. The override now forwards by keyword only.
