## 19.0.0.1.7 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.1.6 (2026-10-03)

- **Fix (REORDER-001): automatic reordering rules are created in the active
  company.** Warehouses and existing rules were searched in the default
  company of the user, so a product created while working in another company
  got a rule on a location of the default company (rejected with a company
  inconsistency error) or no rule at all. The rules now use the company of the
  product or, for shared products, the active company: its warehouses, its
  existing rules and an auto-rule route of that company (or without company);
  the generated rules carry that company.

## 19.0.0.1.5 (2026-10-02)

- **Fix (REORDER-004): the Rules Wizard no longer crashes on save.** Creating
  reorder rules from the product wizard failed with `Invalid field
  'qty_multiple'`, because the field no longer exists on
  `stock.warehouse.orderpoint` in Odoo 19. The wizard no longer sends it (the
  value was always 0); product, location, min/max quantity and trigger are set
  as before.

## 19.0.0.1.4 (2026-09-29)

- Own module icon, instead of the generic gears it had.
