## 20.0.1.2.2 (2026-11-16)

- Empty `__init__.py` restored: the OCA tools (manifestoo, oca-checks-odoo-module) do not
  recognize a module without it, so the CI of the suites that depend on this module failed.
  The module still has no Python code and still imports on Odoo Online.
- Explicit Odoo Online marker: `"online": true` in `static/description/banner.json`
  (the banner no longer infers it from the missing `.py` files).

## 20.0.1.2.1 (2026-11-09)

- The "(importable, Odoo Online)" suffix was removed from the module name. Odoo Apps already shows
  the module as available on Odoo Online (Manifest > Availability), and the Apps banner now carries
  an "Odoo Online" label instead.

## 20.0.1.2.0 (2026-11-08)

- Data-only module: the empty `__init__.py` was removed, so the module has no Python code. It
  can be installed on Odoo Online (Custom plan) as a zip from Apps > Import Module, as well as on
  Odoo.sh and on-premise.
- Odoo Apps does not mark data-only modules as available on Odoo Online, so the module name,
  the summary, the banner and the Apps Store page now say it: "Invoice Product Filter
  (importable, Odoo Online)".

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
