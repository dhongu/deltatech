## 19.0.1.1.3 (2026-11-24)

- Interface texts (button, wizard, server action, error messages, field helps and the
  banner on the expense form) are written in English in the source, with the Romanian
  texts moved to `i18n/ro.po`; users in other languages no longer see Romanian.
  The `.pot` template is added so the module can be translated.

## 19.0.1.1.2 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.1.1 (2026-10-07)

- Apps Store page in English (it was in Romanian): what the module does, with a Usage section,
  and the Romanian translation in its own tab (`readme/*.ro.md`), since the module is meant for
  companies in Romania. Summary in English; support address.

## 19.0.1.1.0 (2026-10-01)

- Imported expenses keep their total with VAT included as the line amount,
  matching the new rule of `deltatech_expenses` (the amount is always gross).
- The screenshot test writes only its own captures (03, 04) into this module.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1 (2026-09-23)

- Overrides that call `super()` without returning its result now pass it on
  (pylint-odoo `missing-return`). The parent methods return `None` today, so the
  behavior is unchanged.
