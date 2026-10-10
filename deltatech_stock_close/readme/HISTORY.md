# Changelog

## 18.0.1.0.6 (2026-10-11)

- Apps Store page: description written from the code (the "close at date" feature, which the module
  does not have, removed; archivable valuation layers and the Only active option of the storage sheet
  described, with a warning that archived layers also leave the product valuation), Configuration and
  Usage added, and the Romanian translation in its own tab (`readme/*.ro.md`). Known bugs in
  `readme/bugs.md`. English summary.
- Module name: "Stock Close" (was "Deltatech Stock Close"), without the brand name, as on 19.0.

## 18.0.1.0.5

- Stop duplicating `do_compute_product()` and the four SQL builders from
  `l10n_ro_stock_report`; only override `_get_sql_select_sold_init/final/in/out`
  and reuse the base queries via `super()`.
- Fix `categ_id` always being `NULL` on generated report lines when
  "Only Active" was checked (the duplicated SQL never joined
  `product_template` nor selected `categ_id`).
- Keep `picking_type_id` and `invoice_date` on stock-in/out lines, now
  populated regardless of the "Only Active" flag (previously lost together
  with `categ_id` in the same duplicated query).

## 18.0.1.0.4

- Replace deprecated `check_access_rights("read")` with `check_access("read")`
  on `account.move.line` (the two ACL methods were merged in Odoo 18.0).
