## 19.0.0.1.5 (2026-10-02)

- **Fix (REORDER-004): the Rules Wizard no longer crashes on save.** Creating
  reorder rules from the product wizard failed with `Invalid field
  'qty_multiple'`, because the field no longer exists on
  `stock.warehouse.orderpoint` in Odoo 19. The wizard no longer sends it (the
  value was always 0); product, location, min/max quantity and trigger are set
  as before.

## 19.0.0.1.4 (2026-09-29)

- Own module icon, instead of the generic gears it had.
