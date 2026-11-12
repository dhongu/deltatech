## 19.0.1.0.10 (2026-11-11)

- Apps Store page: a fuller description (what the module does, the problem it solves, its main functions, dependencies and limits). No change in behavior.

## 19.0.1.0.9 (2026-11-08)

- Test `TestStockPickingReportCompany` creates its product without a company,
  so it no longer fails when `deltatech_product_category` is installed (CI
  shard `stock-2`).

## 19.0.1.0.8 (2026-10-22)

- Listed on Odoo Apps as *Stock Picking Report* (was *Stock Reports*). The technical name `deltatech_stock_report` does not change.

## 19.0.1.0.7 (2026-10-16)

- Picking Analysis report uses the processed quantity (converted into the
  product unit) instead of the demand, for quantity, weight and unit price
  (STOCKREPORT-001).
- Outgoing amounts are negative, like outgoing quantities (STOCKREPORT-002).
- Groups with zero quantity no longer raise a division by zero
  (STOCKREPORT-004).

## 19.0.1.0.6 (2026-10-09)

- Company record rule on the Picking Analysis report: users only see
  pickings of their active companies (STOCKREPORT-003).

## 19.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
