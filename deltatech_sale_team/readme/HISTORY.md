## 20.0.1.0.3 (2026-10-02)

- Migration to 20.0: the record rules are now `ir.access` records in `security/ir.access.csv`.
  The team, personal and "all" rules on invoices, orders, order lines and the sales analysis
  are permissions with the operations previously granted by the access rights. "Own Sales
  Teams" and "Personal Partners" are restrictions that apply only to team managers (without
  "All Documents") and to salesmen (without "Administrator"), respectively, as in 19.0.
- New tests for the team-based access.

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
