## 19.0.1.0.1 (2026-09-18)

- Fix: never round the reorder quantity down to zero. When the needed quantity was smaller than `qty_multiple` and a maximum quantity was set, the Odoo <= 18.0 rounding produced 0, so the rule silently stopped replenishing forever. Such rules now order one full multiple instead of nothing.

## 19.0.1.0.0 (2026-08-21)

- Add: restore `qty_multiple` on `stock.warehouse.orderpoint`, removed by Odoo in 19.0 in favor of `replenishment_uom_id`. Rounds the computed reorder quantity up/down to a multiple, without requiring any per-product/vendor unit of measure setup.
