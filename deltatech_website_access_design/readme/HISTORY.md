# History

## 19.0.1.0.0 (2026-09-24)

- Port from 18.0. Fixed by CI: `data/data.xml` used `res.groups.users` and
  `ir.ui.menu.groups_id`, both renamed on Odoo 19 (`user_ids` and
  `group_ids` respectively) — `ValueError: Invalid field 'users' in
  'res.groups'` at registry load. No other API removed in Odoo 19 is
  touched (no `attrs`/`states`, no `target="inline"`, no search-view
  `<group>`). Ported for Ridacon (helpdesk #9538), which installs it
  standalone (not a `terrabit_ridacon` dependency) to restrict the
  Contacts/Sales/Finance menus to a dedicated internal-access group.
