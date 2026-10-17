# 19.0.1.0.14

- Fix: printing the Declaration of Conformity from a lot or an invoice no
  longer fails for lots without a production date; the declaration date falls
  back to today, as on the delivery report.
- Fix: declarations generated from a lot, invoice or delivery belong to the
  company of the source document (or of the lot), are searched only within
  that company, and the report prints that company as issuer instead of the
  current company. The NRC line is printed only when the field exists.

# 19.0.1.0.13

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.1.0.12 (2026-08-15)

- Fix: added the missing `stock_account` dependency. `report/report_dc.py`
  calls `account.move._get_invoiced_lot_values()`, which is defined in
  `stock_account` (and extended by `sale_stock`). The module only worked when
  another addon in the same database pulled `stock_account` in.
