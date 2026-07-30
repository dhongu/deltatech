## 19.0.1.0.1 (2026-07-30)

- Fix: replaced the deprecated `odoo.osv.expression` import with `odoo.fields.Domain`
  (`expression.AND` → `Domain.AND`). Since 19.0 `odoo.osv` emits a `DeprecationWarning`
  at import time and is scheduled for removal.
