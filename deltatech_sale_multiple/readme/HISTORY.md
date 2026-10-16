## 20.0.1.1.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 20.0.1.1.3 (2026-10-01)

- Migration to Odoo 20.0. The quantity rules are edited on the variant form
  (`product.product_normal_form_view`), the variant easy-edit form no longer
  exists in Odoo 20.

## 19.0.1.1.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.1.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
