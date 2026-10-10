# Known bugs

Review date: 2026-10-11. Target version: Odoo 19.

## STC-001 — P2: Stock moves cannot be closed from the interface

- **Status:** Open. Found on 2026-10-11 while writing the Apps page.
- **Location:** `models/stock_move.py` (`l10n_ro_valuation_active`); no view shows the field.
- **Trigger:** A user wants to close the stock moves of a past period.
- **Actual behavior / impact:** The field exists and the storage sheet filters on it, but it is on no
  form, list or action, so it can only be changed by import or by a script. The former description
  promised to "close stock operations as of a given date", which the module does not do.
- **Suggested fix:** A wizard "Close stock moves until date" (and the field on the stock move list),
  or at least the field in the *Moves History* list.
- **Validation needed:** A user closes the moves until a date and the storage sheet with **Only active**
  leaves them out.
