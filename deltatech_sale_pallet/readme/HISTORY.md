# 19.0.1.0.12

- Apps Store banner (banner.json).

# 19.0.1.0.11

- Fix: pallet count was wrong near multiples of the minimum quantity per
  pallet (e.g. 199.5 units at 100 per pallet rounded down to 2, 100.5 units
  rounded up to 1). Rounding down/up now uses floor/ceiling with a tolerance
  based on the `Product Unit` precision.

# 19.0.1.0.10

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.1.0.9 (2026-08-15)

- Fix: added the missing `stock` dependency. The tests call
  `stock.quant._update_available_quantity()`, which passed only because other
  addons installed alongside brought `stock` into the database.
