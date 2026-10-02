## 19.0.1.2.10 (2026-10-02)

- **Fix (PURCHASEPRICE-002): forced supplier-price update no longer blocks
  confirmation and posting.** With *Force price at validation* enabled,
  confirming a purchase order (always) and posting a vendor bill with a unit
  different from the product unit failed because the code used `product_uom`,
  removed in Odoo 19. Both now use `product_uom_id` and convert the price to the
  unit of the supplier pricing row (e.g. 240 per dozen on the PO is written as
  20 on a supplier row in units).

## 19.0.1.2.9 (2026-09-29)

- Own module icon, instead of the generic gears it had.
