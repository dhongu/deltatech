## 20.0.2.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.2.0.1 (2026-09-23)

- Overrides that call `super()` without returning its result now pass it on
  (pylint-odoo `missing-return`). The parent methods return `None` today, so the
  behavior is unchanged.
