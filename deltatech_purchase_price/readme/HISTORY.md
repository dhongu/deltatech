## 20.0.1.2.10 (2026-10-04)

- **Fix (PURCHASEPRICE-002): forced supplier-price update converts the price
  to the unit of the supplier pricing row.** With *Force price at validation*
  enabled, confirming a purchase order or posting a vendor bill in a unit
  different from the product unit converted the price to the product unit,
  even when the supplier row is in another unit. The price is now converted
  to the unit of the supplier pricing row (e.g. 240 per dozen on the PO is
  written as 20 on a supplier row in units). Port of 19.0.1.2.10
  (dhongu/deltatech#3111); on 20.0 the purchase line and the supplier row use
  `uom_id` (19.0: `product_uom_id`), the removed-field crash of 19.0 did not
  exist on 20.0.
- **Fix (PURCHASEPRICE-001): the automatic sale price update uses the
  currency of the active company.** With *Update list price* enabled, the
  purchase price of a company was treated as an amount in the currency of the
  user's default company, so in a company with another currency the sale
  price was wrong. The cost is now converted from the currency of the active
  company (the one the company-dependent purchase price is read in), with
  that company's rates. Port of 19.0.1.2.11 (dhongu/deltatech#3117).

## 20.0.1.2.9 (2026-09-29)

- Own module icon, instead of the generic gears it had.
