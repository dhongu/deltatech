## 19.0.1.0.13 (2026-10-06)

- Summary in English, as the Apps Store requires, the same as the banner; support address.

## 19.0.1.0.12 (2026-10-03)

- Fixed: invoicing from transfers copied the stock move quantity into the invoice line without unit
  conversion. A purchase line of 1 Dozen received as 12 Units was billed as 12 Dozen (12 times the
  amount), and a partial delivery of 12 Units on a 2 Dozen sale line was invoiced as 2 Dozen. Move
  quantities are now converted from the move unit to the order line unit before summing and before
  the remaining-quantity cap (PICKINV-001). Invoice quantities change whenever the order unit differs
  from the stock move unit.
- Declared the missing `purchase_stock` dependency: the transfer form uses `stock.picking.purchase_id`,
  added by `purchase_stock`, so a standalone install failed with `Field "purchase_id" does not exist`.
  No change on existing databases, where `purchase_stock` is auto-installed with `purchase` and `stock`.

## 19.0.1.0.11 (2026-09-29)

- Own module icon, instead of the generic gears it had.
