## 20.0.1.0.0 (2026-11-17)

- Migrated to 20.0, still data-only (empty `__init__.py`, installs on Odoo Online through Apps > Import
  Module).
- The two global `ir.rule` records became global `ir.access` restrictions (`security/ir.access.csv`,
  no group, operation `r`). Restrictions are AND-ed with the group permissions of `sale` / `account`, so
  the own / all / none tiers behave as on 19.0. The xml ids `sale_report_restrict_rule` and
  `account_invoice_report_restrict_rule` are kept.
- A user in neither group still gets zero rows, not an AccessError: the "no access" branch is now
  `[('id', '=', 0)]`, because on 20.0 a statically false domain such as `[(0, '=', 1)]` makes the whole
  model inaccessible and `search()` raises.
- Tests for the three tiers on Sales Analysis and Invoice Analysis.
- Consultant sheet, USAGE.md and screenshots from 19.0 (#4221), redone on Odoo 20. On 20.0 the
  **Invoiced** button on customers is computed from the invoices, so it is no longer filtered; only
  **Sold** on products is.

## 19.0.1.0.2 (2026-11-14)

- Apps Store banner: the "Odoo Online" badge shows that the module has no Python code and installs on
  Odoo Online.

# 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

# History

## 19.0.1.0.0

- Ported from 18.0 (18.0.1.0.0).
- Fixed two 19.0 breaking changes: `res.groups.category_id` was removed (a
  group's module category is now set via a `res.groups.privilege` record's
  `category_id`, referenced from the group through `privilege_id`), and
  `ir.actions.act_window.groups_id` was renamed to `group_ids`.
