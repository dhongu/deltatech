## 19.0.1.1.7 (2026-10-17)

- Replaces the obsolete `terrabit_product_labels`: on upgrade, a database that still has it installed marks it uninstalled, so Odoo no longer reports it as a module with an inconsistent state. Labels keep working from this module.

## 19.0.1.1.6 (2026-10-16)

- Fixed the barcode on the PDF labels: the image is now embedded as one valid SVG data URI; products without barcode or internal reference no longer break the print.
- Generated lot names are now printed on the labels of incoming transfers before the lots are created.

## 19.0.1.1.5 (2026-10-09)

- Apps Store banner (banner.json).

