# Changelog

## 19.0.1.0.9 (2026-08-15)

- Fix: added the missing `stock` dependency. The tests call
  `stock.quant._update_available_quantity()`, which passed only because other
  addons installed alongside brought `stock` into the database.
