## 19.0.1.0.2 (2026-10-17)

- **Fix: the *Pickup list* report is in the order's Print menu again.** The
  report action had no binding model, so it could not be printed from the order.
- **Fix: the report no longer fails for users with units of measure enabled.**
  It used the field `product_uom`, renamed `product_uom_id` in Odoo 19.
- **Fix: the rack, row and case are taken from the order's warehouse.** They were
  always read from the main warehouse.
- **Fix: the section subtotal no longer fails on orders without a pricelist.**
  It is formatted in the order currency.
- The product image uses the standard image data URI.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
