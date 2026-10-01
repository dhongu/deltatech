# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SECONDARY-001 — P3: Conversion edits leave stored secondary quantities inconsistent

- **Status:** Fixed in 19.0.1.2.0. Priority lowered from P2 to P3 on
  verification (2026-10-01): only the displayed secondary quantity is affected,
  the primary quantity is never changed, and it only happens when a conversion
  is edited. Creating, editing (`uom_qty`, `base_qty`, `uom_id`,
  `product_tmpl_id`) or deleting a conversion now recomputes the stored
  secondary quantity of the lines still open for that product and unit
  (`_recompute_open_secondary_uom_qty` on the conversion, open domain per line
  model in `_get_secondary_uom_open_domain`). Decision: the ratio is live while
  the document can be edited — sale/purchase lines of orders that are neither
  locked nor cancelled (confirmed orders included, their quantities can still
  change and the inverse uses the current ratio) and stock moves not done or
  cancelled. Closed documents (locked or cancelled orders, done or cancelled
  moves) keep the value computed with the ratio valid at that time: they cannot
  be edited, so the inverse cannot disagree with them, and rewriting them would
  change history. No conversion dependency was added on the compute, which
  would have recomputed every historical line. Covered by six tests in
  `tests/test_secondary_uom.py`.
- **Location:** models/secondary_uom_mixin.py; models/sale_order_line.py, purchase_order_line.py, stock_move.py; models/product_uom_conversion.py.
- **Trigger:** Compute a line secondary quantity using 1 alternative unit = 2 base units, then change that product conversion to 1 alternative unit = 4 base units without changing the line primary quantity, product, or selected secondary UoM.
- **Actual behavior:** Stored secondary_uom_qty depends on line quantity/UoM/product/secondary UoM only; the conversion rows and uom_qty/base_qty are not dependencies. Existing values stay based on the old ratio, while an inverse edit uses the new ratio immediately. No conversion write hook invalidates the stored document fields.
- **Evidence:** Source inspection of the stored field, all concrete compute decorators, conversion lookup and forward/inverse methods. For a primary quantity of 10, the forward formula changes from 5 to 2.5 after the ratio edit, but no declared dependency schedules recomputation. No database reproduction was run.
- **Impact:** Displayed secondary quantities disagree with the current conversion and with inverse edits, affecting open sales, purchases, and stock moves.
- **Suggested fix:** Define whether conversion ratios are live or document snapshots. For live ratios, invalidate stored quantities on relevant conversion changes; for snapshots, store the applied ratio on each line and use it consistently for forward and inverse edits.
- **Validation needed:** Edit conversion base_qty/uom_qty, add/remove a conversion, and edit secondary quantity afterward on sale, purchase and stock lines; explicitly verify the intended behavior for historical documents.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. SECONDARY-001 was fixed and verified with database tests on 2026-10-01.
