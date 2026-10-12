## 19.0.1.1.2 (2026-10-10)

- Apps Store page: description written from the code (the "close at date" feature, which the module
  does not have, removed; the Valuation Active flag and the Only active option of the storage sheet
  described), Configuration and Usage added, and the Romanian translation in its own tab
  (`readme/*.ro.md`). Known bugs in `readme/bugs.md`. English summary; banner aligned.
- Module name: "Stock Close" (was "Deltatech Stock Close"), without the brand name and the same as the
  banner.

# 19.0.1.1.1

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.1.0.0

- Port to Odoo 19.0 from 18.0.
- Uses `check_access("read")` (the deprecated `check_access_rights` was removed
  in favor of the merged `check_access` method).
