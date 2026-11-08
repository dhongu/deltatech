## 20.0.2.1.0 (2026-11-08)

- Data-only module: the empty `__init__.py` files (module and `tests/`) were removed, so the
  module has no Python code at all. It can be installed on Odoo Online (Custom plan) as a zip
  from Apps > Import Module, as well as on Odoo.sh and on-premise.
- Odoo Apps does not mark data-only modules as available on Odoo Online, so the module name,
  the summary, the banner and the Apps Store page now say it: "No Quick Create (importable,
  Odoo Online)".

## 19.0.2.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
