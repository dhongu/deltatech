## 20.0.1.0.3 (2026-10-02)

- Migration to Odoo 20.0: the "Available" column on the order lines is now placed before
  the quantity column (`sol_qty`), as the quantity field is no longer a direct child of the
  lines list.
- Fix: the "Is Ready" search filter returned the orders that are *not* ready (the search
  method expected `=` while the ORM sends `in`).
- Tests with assertions for the ready state (quotations and confirmed orders, both picking
  policies), the search filter and the availability text.

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
