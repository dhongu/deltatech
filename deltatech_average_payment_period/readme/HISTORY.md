## 19.0.1.0.7 (2026-11-19)

- Average Payment Period report: the pivot now shows the amount-weighted average of Payment Days,
  like the graph; before, the pivot showed a plain average (the weighting was only applied to
  `_read_group`, while the Odoo 19 pivot reads through `_read_grouping_sets`).
- Dedicated graph view, opening on the Payment Days measure.
- Consultant sheet (`readme/FISA_CONSULTANT.md`) with screenshots, `readme/USAGE.md` rewritten in
  English with the English screenshots, `readme/DESCRIPTION.md` aligned with the code.

## 19.0.1.0.6 (2026-11-19)

- Payment date and payment days on journal items are reset when the full
  reconciliation is removed; before, the old values stayed on the unpaid
  item (AVGPAY-001).
- Payment date and payment days are recomputed when an item is reconciled
  again: Odoo 19 links the full reconciliation through SQL, so the stored
  fields were not refreshed.

## 19.0.1.0.5 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 19.0.1.0.4 (2026-10-09)

- Average Payment Period report: company field and company record rule, users
  only see journal items of their active companies (AVGPAY-002).

## 19.0.1.0.3 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
