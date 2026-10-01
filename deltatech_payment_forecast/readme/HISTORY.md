## 20.0.0.0.4 (2026-10-01)

- Migration to Odoo 20.0: access rights and the multi-company restriction of the forecast lines in `security/ir.access.csv` (replaces `ir.model.access.csv` and the `ir.rule`).

## 19.0.0.0.3 (2026-10-01)

- Forecast lines carry the company currency, the currency of the signed invoice amounts (FORECAST-001).
- Forecast lines have a company and a multi-company record rule. A recalculation replaces only the rows of its own company, and the scheduled action runs for each company (FORECAST-002).
- The wizard company filters the invoices and the payment history (FORECAST-003).

## 19.0.0.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
