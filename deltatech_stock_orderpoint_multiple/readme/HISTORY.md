## 19.0.1.0.0 (2026-08-21)

- Add: restore `qty_multiple` on `stock.warehouse.orderpoint`, removed by Odoo in 19.0 in favor of `replenishment_uom_id`. Rounds the computed reorder quantity up/down to a multiple, without requiring any per-product/vendor unit of measure setup.
