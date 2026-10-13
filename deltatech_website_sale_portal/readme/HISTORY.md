## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.1.0.1 (2026-07-30)

- Fix: replaced the deprecated `odoo.osv.expression` import with `odoo.fields.Domain`
  (`expression.AND` → `Domain.AND`). Since 19.0 `odoo.osv` emits a `DeprecationWarning`
  at import time and is scheduled for removal.
