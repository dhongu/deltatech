## 20.0.1.0.10 (2026-11-04)

- Migration to Odoo 20.0: `_change_standard_price` follows the new signature (creating a product
  with a cost no longer fails); the transfer amount uses the magnitude of the move value (negative
  on outgoing moves in 20).

## 19.0.1.0.10 (2026-11-03)

- Description rewritten from the code: the transfer value is shown in the transfers list, not on the transfer form.
- Documented the account propagation to subcategories and the Change Product Price group, which the old description did not mention.
- Summary and banner corrected.

## 19.0.1.0.9 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.8 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.7 (2026-10-08)

- Fixed STOCKACCOUNT-001: saving a stock valuation account on a category, the
  *Propagate Accounts* action and selecting a parent category raised
  `AttributeError`, because they still used fields removed in Odoo 19 (old
  price difference account, stock input/output accounts). Propagation now uses
  the Odoo 19 fields: price difference, expense, income and stock valuation
  accounts, stock journal, costing method and inventory valuation.

## 19.0.1.0.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.
