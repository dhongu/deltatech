## 19.0.1.2.12 (2026-10-06)

- **New vendor pricing rows no longer take the product cost as unit price.**
  On the *Purchase* tab of a product (template or variant), a new vendor line
  was pre-filled with the product cost (e.g. 99.01), which was easy to save by
  mistake as the vendor price. The unit price of a new line now starts at 0.

## 19.0.1.2.11 (2026-10-03)

- **Fix (PURCHASEPRICE-001): the automatic sale price update uses the
  currency of the active company.** With *Update list price* enabled, the
  purchase price of a company was treated as an amount in the currency of the
  user's default company, so in a company with another currency the sale price
  was wrong (e.g. a cost of 100 EUR with a 100% markup became 40 EUR instead
  of 200 EUR). The cost is now converted from the currency of the company in
  which it was recorded, with that company's rates. Sale prices updated from
  now on in a company whose currency differs from the default company of the
  user will have different (correct) values.

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
