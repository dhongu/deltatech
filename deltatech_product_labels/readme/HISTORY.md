## 20.0.1.2.0 (2026-10-22)

- New default layouts with their own paper format: A4 sheet of 3x8 labels (70x37 mm), and thermal labels
  of 100x50 mm and 40x25 mm, one label per page. The 100x50 layout no longer prints on an A4 page.
- The wizard proposes the layout printed last by the user; the first time, the A4 3x8 sheet.
- Preview for the ZPL (text) layouts: the labels are converted to PDF with the Labelary service, as for
  the AWB labels. The size of the label is set on the layout or read from its name (e.g. "40x30").
- Generated lot names are now printed on the labels of incoming transfers before the lots are created.
- Replaces the obsolete `terrabit_product_labels`: on upgrade, a database that still has it installed marks
  it uninstalled, so Odoo no longer reports it as a module with an inconsistent state.
- Consultant sheet (`readme/FISA_CONSULTANT.md`) with screenshots.

## 20.0.1.1.6 (2026-10-22)

- License changed from AGPL-3 to OPL-1, so the Terrabit modules under OPL-1 or LGPL-3 can depend on
  it (Odoo Apps does not allow them to depend on an AGPL-3 module). The module stays free.

## 20.0.1.1.5 (2026-10-09)

- Apps Store banner (banner.json).

