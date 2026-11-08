## 19.0.1.1.0 (2026-11-08)

- Data-only module: the empty `__init__.py` was removed, so the module has no Python code at
  runtime (`tests/` stays, for the JavaScript test in CI). It can be installed on Odoo Online
  (Custom plan) as a zip from Apps > Import Module, as well as on Odoo.sh and on-premise.
- The JavaScript test is listed by name in the manifest assets: an imported module does not
  accept wildcards (`**/*`) in asset paths. The obsolete `qweb` key, pointing to a folder that
  does not exist, was removed.
- Odoo Apps does not mark data-only modules as available on Odoo Online, so the module name,
  the summary, the banner and the Apps Store page now say it: "List View Select Text
  (importable, Odoo Online)".

## 19.0.1.0.5 (2026-10-19)

- Fixed the `invalid input syntax for type integer: "virtual_N"` error when saving a form
  (e.g. the stock return wizard) after a one2many line that was never saved got deleted
  twice, for instance with Enter pressed twice on its trash icon: the second delete no
  longer sends a `DELETE` command with the line's virtual id to the server.

## 19.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.3 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
