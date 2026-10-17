## 19.0.0.0.4 (2026-10-17)

- Fixed MRPDATE-001: the validation date was written on every *Mark as Done*
  click, even when Odoo first opened a wizard (backorder, consumption) and the
  order stayed unfinished after the wizard was cancelled. The date is now set
  only on the orders actually done, in the user's timezone, and the date of an
  order already done is kept.

## 19.0.0.0.3 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

## 19.0.0.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
