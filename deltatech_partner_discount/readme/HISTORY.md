## 19.0.1.0.3 (2026-10-08)

- Fixed PARTNERDISC-001: users outside *Can modify partner discount* could
  still change the proposed discount of an existing partner by import, RPC or
  any server-side write, because only the form onchange checked the group.
  The check is now done on write as well. Creating a partner with a negative
  discount (or one coming from a context default) is also refused for these
  users. Saving a partner without changing its discount is still allowed.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1 (2026-09-24)

- Port to Odoo 19: `_()` replaced with `self.env._()`, the Odoo 19 convention
  (pylint-odoo `prefer-env-translation`). The rest of the code is unchanged —
  none of the APIs used (`fields.Float`, `api.onchange`, `api.model_create_multi`,
  `has_group`) changed on O19.
- Fix: `security/groups.xml` set `category_id` on `res.groups`, a field
  removed in Odoo 19 (`ValueError: Invalid field 'category_id' in
  'res.groups'` when loading the registry, caught by the CI tests). Removed.
- Fix: the tests used `groups_id` when creating `res.users`, a field
  renamed to `group_ids` in Odoo 19 (`ValueError: Invalid field
  'groups_id' in 'res.users'`, also caught by CI).
