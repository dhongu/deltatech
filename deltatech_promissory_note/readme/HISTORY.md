## 19.0.1.0.8 (2026-10-13)

- The tests run again: they had been switched off since the migration to 19.0,
  because the form requires both banks and the tests did not fill them in. They
  now also check the issuer/beneficiary set by the note type, the state changes
  and the notification sent when the last note is cashed.

## 19.0.1.0.7 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.5 (2026-09-24)

- Romanian translations for the messages recovered in the previous release
  (messages that babel could not extract while the file contained an f-string
  inside `_()`); the `.pot` now lists them too.

## 19.0.1.0.4 (2026-09-24)

- Translatable messages built with f-strings inside `_()` / `self.env._()` now use a
  fixed text with named placeholders. An f-string can never be translated, and
  babel stopped at the first one, dropping every other message of the file from the
  `.pot`: those messages are now exported for translation again.
