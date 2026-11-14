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
