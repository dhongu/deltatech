## 19.0.0.1.11 (2026-10-22)

- Listed on Odoo Apps as *Auto Reorder Rules* (was *Auto Reorder Rule*). The technical name `deltatech_auto_reorder_rule` does not change.

## 19.0.0.1.10 (2026-10-16)

- **Fix (#3364): a rule in one warehouse no longer blocks the others.** Create
  rule skipped the product entirely when it already had a rule in any
  warehouse of the company, so a warehouse enabled later never got its rule.
  Each warehouse is now checked separately: missing rules are created, the
  existing ones are kept and no duplicates are added.
- **Fix (#3365): the system parameter `dont_auto_create_rule` set to `False`
  no longer disables the automatic rules.** The value is now read as a
  boolean: only `True`/`1`/`yes` disable the creation of rules for new
  products.
- **Fix (#3366): the Rules Wizard creates the rules in the company of each
  location.** Selecting a location of another allowed company failed with a
  company inconsistency error; the rule now gets the company of its location
  and an auto-rule route of that company (or without company).

## 19.0.0.1.9 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.0.1.8 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

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
