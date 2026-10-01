## 20.0.2.0.2 (2026-10-01)

- Migration to 20.0, including the automatic receipt fix (RECEIPT-001). Adapted to the
  Odoo 20 API: units of measure on purchase lines and stock moves are `uom_id`, and the
  return picking for negative purchase lines is created explicitly, since
  `purchase.order._prepare_picking()` no longer exists. The return moves now carry the
  unit of measure in which their quantity is expressed.

## 19.0.2.0.2 (2026-10-01)

- Automatic receipt no longer deletes the receipt moves (RECEIPT-001): the ordered quantity is set on each move with a demand and the move is marked as picked, so posting the vendor bill really receives the goods in stock.

## 19.0.2.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
