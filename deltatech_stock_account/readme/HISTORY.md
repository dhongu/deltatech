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
