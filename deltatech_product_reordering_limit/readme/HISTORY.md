## 19.0.1.0.6 (2026-10-22)

- Listed on Odoo Apps as *Product Reordering Limits* (was *Product Reordering Limit*). The technical name `deltatech_product_reordering_limit` does not change.

## 19.0.1.0.5

- Fix: the "Below Minimum" filter counted stock from all companies, warehouses
  and locations, so a product could show as below minimum on its form but be
  missing from the filter. The filter now uses the same stock quantity as the
  product (allowed companies and the selected warehouse/location).

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
