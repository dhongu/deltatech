## 19.0.1.0.3 (2026-10-17)

- The Delivery button now shows on customer invoices and credit notes, and the
  Reception button on vendor bills and refunds; before, both were always hidden.

## 19.0.1.0.2 (2026-10-01)

- Declare `sale_stock` and `purchase_stock` as dependencies: the invoice button reads
  the stock moves of sale and purchase lines, which these modules provide.
- Tests run post-install on the standard accounting test setup and also cover
  sale invoices and invoices without deliveries.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
