# History

## 18.0.1.0.3 (2026-07-30)

- Fixed `?ppg=` silently filtering the shop by price. The `shop()` override
  declared `(page, category, search, ppg)` and forwarded those positionally,
  but core's fourth parameter is `min_price`, so `?ppg=40` reached it as
  `min_price=40` and dropped every cheaper product from the listing while the
  page size stayed at its default. The override now names only the parameters
  it reads and forwards the rest by keyword, which also survives the 19.0
  signature where `ppg` became `tags`.
