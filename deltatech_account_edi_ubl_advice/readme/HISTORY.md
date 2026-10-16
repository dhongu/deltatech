## 19.0.1.0.3 (2026-10-09)

- The UBL export no longer fails on databases with Sales but without Inventory
  or the Sales-Inventory integration (`sale_stock`): the despatch advice
  reference is simply left out. With `sale_stock`, the delivered transfers are
  referenced as before.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
