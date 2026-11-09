## 20.0.1.1.2 (2026-11-09)

- The "(importable, Odoo Online)" suffix was removed from the module name. Odoo Apps already shows
  the module as available on Odoo Online (Manifest > Availability), and the Apps banner now carries
  an "Odoo Online" label instead.

## 20.0.1.1.1 (2026-11-08)

- Odoo Apps does not mark data-only modules as available on Odoo Online, so the module name,
  the summary, the banner and the Apps Store page now say it: "Report Layout (importable,
  Odoo Online)".

## 20.0.1.1.0 (2026-11-08)

- Migration to 20.0. Odoo 20 dropped the layout background (`layout_background`
  on the company), so Style1 and Style2 no longer read it. The document body follows
  the standard `web.external_layout_body` of 20.0 (hidden heading for multiple
  invoice sending, `hide_title`, custom address block), and the layout colors are
  inserted next to the other layout-specific styles of `web.styles_company_report`.
- Still data-only, importable on Odoo Online from Apps > Import Module.

## 19.0.1.1.0 (2026-11-08)

- Data-only module: the empty `__init__.py` was removed, so the module has no Python
  code at all. It can be installed on Odoo Online (Custom plan) as a zip from
  Apps > Import Module, as well as on Odoo.sh and on-premise.
- Consultant sheet (readme/FISA_CONSULTANT.md), USAGE.md and screenshots; the usage steps moved
  from DESCRIPTION.md to USAGE.md.
- The report styles are listed one by one in the manifest assets: an imported module
  does not accept wildcards (`**/*`) in asset paths.

## 19.0.1.0.2 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
