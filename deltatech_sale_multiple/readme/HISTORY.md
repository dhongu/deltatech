## 19.0.1.1.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.1.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
