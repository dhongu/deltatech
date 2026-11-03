## 20.0.2.0.3 (2026-11-03)

- Description rewritten after the code: the generic partner is declared in the
  Sales settings, section Invoicing, and is not selected automatically in
  sales or invoicing as the old text said. The banner no longer promises it.
- Limitations: on 20.0 the journal restriction does not apply in the Register
  Payment wizard and does not replace a restricted default journal.

## 20.0.2.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.2.0.1 (2026-09-23)

- Overrides that call `super()` without returning its result now pass it on
  (pylint-odoo `missing-return`). The parent methods return `None` today, so the
  behavior is unchanged.
