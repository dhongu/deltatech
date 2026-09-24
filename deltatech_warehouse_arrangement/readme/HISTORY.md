## 19.0.0.1.4 (2026-09-24)

- Translatable messages built with f-strings inside `_()` / `self.env._()` now use a
  fixed text with named placeholders. An f-string can never be translated, and
  babel stopped at the first one, dropping every other message of the file from the
  `.pot`: those messages are now exported for translation again.

## 19.0.0.1.3 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
