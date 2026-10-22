## 19.0.1.3.1 (2026-10-22)

- Without a price list, the price on the labels uses the currency of the product (of its company).
- Consultant sheet: the label screenshots and texts show the price including VAT.

## 19.0.1.3.0 (2026-10-22)

- The default layouts (A4 3x8, 100x50, 40x25) print the price including taxes (VAT), with its currency
  and unit of measure, next to the product name, internal reference, lot and barcode: they can be used
  as shelf labels in the shop, in the warehouse or on the product. Without a price, no price is printed.
- The price including taxes (`price_incl`) moves here from `deltatech_price_change_label`; the price
  uses the currency of the price list chosen in the wizard.

## 19.0.1.2.0 (2026-10-22)

- New default layouts with their own paper format: A4 sheet of 3x8 labels (70x37 mm), and thermal labels
  of 100x50 mm and 40x25 mm, one label per page. The 100x50 layout no longer prints on an A4 page.
- The wizard proposes the layout printed last by the user; the first time, the A4 3x8 sheet.
- Preview for the ZPL (text) layouts: the labels are converted to PDF with the Labelary service, as for
  the AWB labels. The size of the label is set on the layout or read from its name (e.g. "40x30").

## 19.0.1.1.9 (2026-10-22)

- License changed from AGPL-3 to OPL-1, so the Terrabit modules under OPL-1 or LGPL-3 can depend on
  it (Odoo Apps does not allow them to depend on an AGPL-3 module). The module stays free.

## 19.0.1.1.8 (2026-10-17)

- Replaced the deprecated `t-raw="0"` directive with `t-out="0"` in the label layout, removing the deprecation warning logged at every print.

## 19.0.1.1.7 (2026-10-17)

- Replaces the obsolete `terrabit_product_labels`: on upgrade, a database that still has it installed marks it uninstalled, so Odoo no longer reports it as a module with an inconsistent state. Labels keep working from this module.

## 19.0.1.1.6 (2026-10-16)

- Fixed the barcode on the PDF labels: the image is now embedded as one valid SVG data URI; products without barcode or internal reference no longer break the print.
- Generated lot names are now printed on the labels of incoming transfers before the lots are created.

## 19.0.1.1.5 (2026-10-09)

- Apps Store banner (banner.json).

