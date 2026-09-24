# History

## 19.0.1.0.0 (2026-09-24)

- Port from 18.0. No code changes: `data/data.xml` (the only data file) does
  not use any API removed in Odoo 19 (no `attrs`/`states`, no `target="inline"`,
  no search-view `<group>`). Ported for Ridacon (helpdesk #9538), which
  installs it standalone (not a `terrabit_ridacon` dependency) to restrict the
  Contacts/Sales/Finance menus to a dedicated internal-access group.
