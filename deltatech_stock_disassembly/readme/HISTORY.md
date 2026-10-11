## 20.0.1.0.0 (2026-10-12)

- Migration to Odoo 20: the value of a stock move is signed (negative for the disassembled
  product), `_get_value_from_production` no longer takes `at_date`, the moves and move lines use
  `uom_id`, the quantities are compared with `uom.compare` (`uom.uom.rounding` is gone), a product
  without tracking has `tracking` empty (no more `'none'`) and the access rights are in
  `ir.access`.

## 19.0.1.0.0 (2026-10-12)

- New module: disassembly report without a bill of materials. The disassembled product leaves the
  stock at its actual cost, which is split over the resulting products (by quantity, reference
  price, percentages or fixed values, rounding on the last line); losses within or above the norm;
  one journal entry per report, with the Romanian account correspondences by synthetic account
  (34x through 711, 371 → 30x and 30x → 30y only by company setting, other pairs refused);
  PDF report with the signatures of the committee.
