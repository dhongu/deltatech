## 20.0.1.0.3 (2026-11-03)

- Description, summary and banner rewritten after the code: the widget is a
  preview, not an icon picker; Font Awesome names are rendered through the
  Material Symbols mapping of Odoo 20, and Material Symbols names are accepted.

## 20.0.1.0.2 (2026-10-12)

- Migration to 20.0: Font Awesome is no longer shipped with Odoo 20, so the widget renders Material Symbols icons (`<i class="oi" data-icon="..."/>`). Stored Font Awesome values (`fa-globe`, `fa fa-globe`, `globe`) are translated with the official FA -> Material Symbols mapping; a Material Symbols name (`public`) can also be stored directly. Props declared with `useProps` (Owl 3). Empty values no longer raise an error.

## 19.0.1.0.2 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
