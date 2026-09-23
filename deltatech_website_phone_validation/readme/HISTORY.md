## 19.0.1.0.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.1.0.1 (2026-08-13)

- Fix: `_validate_address_values` still required `is_main_address`, a parameter Odoo 19 no longer passes - the 19.0 migration kept the 18.0 signature. Any address submitted from the website raised a `TypeError` (500) as soon as this module was installed. The parameter is dropped; anything else the caller adds still travels through `**_kwargs`.
