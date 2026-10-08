## 19.0.2.0.3 (2026-10-08)

- Fixed RECEIPT-002: recomputing the return moves of a negative purchase line
  failed with `AttributeError` once a stock move existed, because it read
  `product_uom_id` on the stock move (the Odoo 19 field is `product_uom`). The
  quantity already returned was also counted with the wrong sign, so a return
  raised from 5 to 7 would have requested 12 more units instead of 2.
- Fixed RECEIPT-003: with *Propagate units of measure* enabled, a return in a
  purchase unit different from the product unit lost its unit: 2 dozens were
  returned as 2 units. The return move now keeps the unit computed for it.
- Fixed RECEIPT-004: approving several purchase orders together, when one of
  them had a negative line, failed with *Expected singleton*. Each return
  transfer now takes the operation type, location and supplier of its own order.

## 19.0.2.0.2 (2026-10-01)

- Automatic receipt no longer deletes the receipt moves (RECEIPT-001): the ordered quantity is set on each move with a demand and the move is marked as picked, so posting the vendor bill really receives the goods in stock.

## 19.0.2.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
