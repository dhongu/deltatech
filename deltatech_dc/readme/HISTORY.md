# Changelog

## 19.0.1.0.12 (2026-08-15)

- Fix: added the missing `stock_account` dependency. `report/report_dc.py`
  calls `account.move._get_invoiced_lot_values()`, which is defined in
  `stock_account` (and extended by `sale_stock`). The module only worked when
  another addon in the same database pulled `stock_account` in.
