## 20.0.1.3.1 (2026-11-16)

- Empty `__init__.py` restored: the OCA tools (manifestoo, oca-checks-odoo-module) do not
  recognize a module without it, so the CI of the suites that depend on this module failed.
  The module still has no Python code and still imports on Odoo Online.
- Explicit Odoo Online marker: `"online": true` in `static/description/banner.json`
  (the banner no longer infers it from the missing `.py` files).

## 20.0.1.3.0 (2026-11-16)

- Three more report layouts: Compact Header (small font, tight margins, one-line header, for
  documents with many lines), Minimal (black and white, no color bands, cheap to print)
  and Accent (colored vertical bar along the left edge of the content, colored title).
- Consultant sheet, USAGE and DESCRIPTION updated for the eight layouts (Style1, Style2, Band, Modern, Title Box, Compact Header, Minimal, Accent), with new screenshots and a demo GIF.
- The Compact layout is named **Compact Header**, so it is not confused with the standard Odoo 20 **Compact** layout.

## 20.0.1.2.0 (2026-11-16)

- Three new report layouts: Band (full-width colored header band and footer band),
  Modern (logo left, title and company details right, colored total bar) and Title Box
  (boxed centered title, colored table header). Colors follow the company's primary/secondary colors.

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
