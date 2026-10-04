## 19.0.0.1.8 (2026-10-04)

- Fix the full name of storehouses: it showed only the stock location name, without the storehouse name.
- Fix the full name of zones, shelves, sections and racks when a parent level is not set: the missing level is
  now skipped instead of raising an error when the record name was displayed.
- Fix lot creation: locations given explicitly for the lot are no longer replaced by the product's ones
  (ARRANGE-002), each lot in a batch now takes the locations of its own product, and creating a lot without a
  product no longer fails with an internal error.
- Lot change location wizard: scanning a new lot clears the rack chosen for the previous one, so it cannot be
  applied to the wrong lot by mistake (ARRANGE-001); an ambiguous lot name now shows an error instead of being
  ignored.

## 19.0.0.1.7 (2026-10-04)

- Add unit tests covering the location hierarchy names, lot location defaults on create,
  the lot location update on stock moves into/out of the master location and the
  lot change location barcode wizard.

## 19.0.0.1.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.0.1.5 (2026-09-24)

- Romanian translations for the messages recovered in the previous release
  (messages that babel could not extract while the file contained an f-string
  inside `_()`); the `.pot` now lists them too.

## 19.0.0.1.4 (2026-09-24)

- Translatable messages built with f-strings inside `_()` / `self.env._()` now use a
  fixed text with named placeholders. An f-string can never be translated, and
  babel stopped at the first one, dropping every other message of the file from the
  `.pot`: those messages are now exported for translation again.

## 19.0.0.1.3 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
