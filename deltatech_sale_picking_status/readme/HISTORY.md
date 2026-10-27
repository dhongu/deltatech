## 20.0.2.0.2 (2026-10-22)

- Listed on Odoo Apps as *Sale Delivery Status* (was *Sale order picking status*). The technical name `deltatech_sale_picking_status` does not change.

## 20.0.2.0.1 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 20.0.2.0.0 (2026-10-03)

- The module becomes an extension of the standard `delivery_status`: the own
  `picking_status` field and the overrides on `stock.picking` are removed.
- Filters by delivery status, list column shown by default, tracking in the
  chatter.
- Migration: saved filters (`ir.filters`) and export templates on
  `picking_status` are rewritten on `delivery_status`; views edited in the
  database that still use the old field are reported in the log.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
