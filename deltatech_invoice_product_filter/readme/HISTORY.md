## 19.0.1.2.1 (2026-11-09)

- The "(importable, Odoo Online)" suffix was removed from the module name. Odoo Apps already shows
  the module as available on Odoo Online (Manifest > Availability), and the Apps banner now carries
  an "Odoo Online" label instead.

## 19.0.1.2.0 (2026-11-08)

- Data-only module: the empty `__init__.py` was removed, so the module has no Python code. It
  can be installed on Odoo Online (Custom plan) as a zip from Apps > Import Module, as well as on
  Odoo.sh and on-premise.
- Odoo Apps does not mark data-only modules as available on Odoo Online, so the module name,
  the summary, the banner and the Apps Store page now say it: "Invoice Product Filter
  (importable, Odoo Online)".

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
