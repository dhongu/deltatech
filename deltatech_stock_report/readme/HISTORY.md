## 20.0.1.0.7 (2026-10-22)

- Listed on Odoo Apps as *Stock Picking Report* (was *Stock Reports*). The technical name `deltatech_stock_report` does not change.

## 20.0.1.0.6 (2026-10-10)

- Fix STOCKREPORT-003: the *Stock picking report* (SQL view) selected the transfers of every company and had no company restriction, so a stock manager restricted to one company could read quantities, values and partners of other companies. A global restriction `[('company_id', 'in', company_ids)]` is added in `security/ir.access.csv`.

## 20.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
