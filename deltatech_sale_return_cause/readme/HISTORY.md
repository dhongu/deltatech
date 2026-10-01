## 20.0.0.0.10 (2026-10-01)

- Migration to Odoo 20.0, including the RETURNCAUSE-001 fix from 19.0.0.0.10.
- The sales analysis report uses the new `_select_dict` / `_groupby_list` hooks of `sale.report`.
- The automatic return amount setting is read as a boolean config parameter.

## 19.0.0.0.10 (2026-10-01)

- Setting the return cause on several orders at once no longer fails with "Expected singleton": orders that
  already have a return cause date keep it, only the others get today's date, and a date given explicitly is kept.
- Recalculating the return amount on several orders uses the credit notes of each order.

## 19.0.0.0.9 (2026-09-29)

- Own module icon, instead of the generic gears it had.
