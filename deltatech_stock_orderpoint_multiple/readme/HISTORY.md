## 20.0.1.0.4 (2026-10-28)

- Migrated to Odoo 20.0. Quantities are compared with the *Product Unit* decimal precision
  (the unit of measure no longer has a rounding).

## 19.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.3 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1 (2026-09-18)

- Fix: never round the reorder quantity down to zero. When the needed quantity was smaller than `qty_multiple` and a maximum quantity was set, the Odoo <= 18.0 rounding produced 0, so the rule silently stopped replenishing forever. Such rules now order one full multiple instead of nothing.

## 19.0.1.0.0 (2026-08-21)

- Add: restore `qty_multiple` on `stock.warehouse.orderpoint`, removed by Odoo in 19.0 in favor of `replenishment_uom_id`. Rounds the computed reorder quantity up/down to a multiple, without requiring any per-product/vendor unit of measure setup.
