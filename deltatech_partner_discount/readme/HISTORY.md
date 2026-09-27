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
