## 19.0.1.0.4

- Add unit tests covering the reordering limit fields, the below-minimum compute and
  search, and the XLSX reordering report wizard.

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.2 (2026-08-14)

- Fix: `action_generate_report` crashed with a `TypeError` when the wizard was
  opened without a product selection. It called `browse()` on
  `context.get("active_ids")`, which is `None` outside the list-view binding.
  The selection is now read through `_get_products`, which also checks
  `active_model`, so `active_ids` coming from another model can no longer be
  browsed as product templates and silently produce a report about unrelated
  records. With no product selected the wizard now raises a clear
  `UserError` instead of failing.

## 19.0.1.0.1

- Migration to Odoo 19.0.
