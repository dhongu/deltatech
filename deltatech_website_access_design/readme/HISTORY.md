## 19.0.1.1.0 (2026-11-07)

- Installation no longer hides Contacts, Sales and Invoicing > Customers /
  Vendors from every user except the administrator: all internal users existing
  at installation join the group *Access Partners, Sale, Invoice*. The menus are
  restricted once, at installation, and a module update no longer overwrites
  their groups. Uninstalling gives the menus back their standard groups.
  Existing installations keep their current setup. The description explains
  how to give the web designer the standard *Website: Restricted Editor* right.

## 19.0.1.0.2 (2026-11-03)

- Description rewritten from the code: the module grants no website rights; it
  reserves the Contacts, Sales and Invoicing > Customers / Vendors menus to the
  group *Access Partners, Sale, Invoice*. Documented the limitations after a
  Contacts update and at uninstall.

# 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

# History

## 19.0.1.0.0 (2026-09-24)

- Port from 18.0. Fixed by CI: `data/data.xml` used `res.groups.users` and
  `ir.ui.menu.groups_id`, both renamed on Odoo 19 (`user_ids` and
  `group_ids` respectively) — `ValueError: Invalid field 'users' in
  'res.groups'` at registry load. No other API removed in Odoo 19 is
  touched (no `attrs`/`states`, no `target="inline"`, no search-view
  `<group>`). Ported for a customer, who installs it
  standalone (not as a dependency of a customer module) to restrict the
  Contacts/Sales/Finance menus to a dedicated internal-access group.
