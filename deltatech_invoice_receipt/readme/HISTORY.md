## 20.0.2.0.5 (2026-11-06)

- Port of 19.0.2.0.4: the discount of the bill line is copied to the purchase order
  line generated from the bill (5 x 100 with 10% discount is 450 on the order, not 500).
  The limitation is removed from the description.

## 20.0.2.0.4 (2026-11-03)

- Description rewritten from the code: the purchase order created from the bill stays a request
  for quotation and must be confirmed before the bill can be posted; it is not confirmed
  automatically.
- Documented the return transfer created for negative purchase lines and the limitations (credit
  notes, regular orders, discount not copied to the purchase order).
- Summary typo fixed; banner corrected.

## 20.0.2.0.3 (2026-10-08)

- Returns to the vendor from negative purchase lines: the quantity already returned is now
  subtracted from the requested return (it was added, so raising a return of 5 to 7
  requested 12 more units instead of 2). Port of the 19.0 fix.

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
