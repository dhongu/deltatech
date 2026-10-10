## 20.0.1.0.4 (2026-10-10)

- Fix AVGPAY-002: the *Average payment period* report (SQL view) selected the journal items of every company and had no company restriction, exposing invoices, payment history and amounts of other companies. The view now exposes `company_id` (query built with `SQL()`) and a global restriction `[('company_id', 'in', company_ids)]` is added in `security/ir.access.csv`.

## 20.0.1.0.3 (2026-10-01)

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
