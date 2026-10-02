# Bug review — Batch Transfer

Review date: 2026-10-02. Target version: Odoo 19.

## BATCHTRANSFER-001 — P1: Batch quantity preparation uses a removed move-line field

- **Status:** Fixed in 19.0.0.0.5 — the allocation was rewritten on the Odoo 19 move line API in a shared `_allocate_line_quantities()`: the capacity of every move line is its current `quantity` (reserved), read before any change, never the demand of the parent move; wizard quantities (product unit) are converted to the move line unit; the rest goes to `additional_quantity`. With Set Done Qty the allocated lines get `quantity` + `picked=True` (without product lines the reserved lines are marked picked); without it only the requested quantities stay reserved, unpicked. Covered by tests in `tests/test_prepare_batch.py` (both modes, with and without product lines, two move lines, extra quantity, dozens vs units, unknown product, full purchase flow).
- **Location:** wizard/stock_prepare_batch.py, prepare_lines_and_set_quantity() and prepare_lines_and_wo_quantity().
- **Trigger:** Confirm a batch preparation with Set Done Qty enabled and existing move lines, or provide product quantities to either preparation mode.
- **Actual behavior:** Both methods read stock.move.line.product_uom_qty; the without-done-quantity path also writes that field. Odoo 19 has quantity and a linked move_id whose product_uom_qty represents demand, but no product_uom_qty field on stock.move.line. These paths raise AttributeError/invalid-field errors and roll back batch preparation.
- **Evidence:** Executed the actual AST-extracted set-quantity method with no wizard product lines and one native-shaped move line: AttributeError for product_uom_qty. Inspected local stock.move.line declaration and all occurrences: demand references use move_id.product_uom_qty, not a move-line field. Both wizard methods retain the obsolete accesses.
- **Impact:** Quantity-driven batch preparation fails instead of opening a prepared batch.
- **Suggested fix:** Redesign allocation using the current reservation/quantity API, preserving per-lot and per-unit semantics; do not blindly copy parent move demand to every move line.
- **Validation needed:** Both wizard modes, empty/nonempty product lines, multiple lot lines, partial reservations, additional quantities and differing units.

## Review limitations

All eligible Python/XML source and the access CSV were read. Extracted-method mock execution only; no Odoo batch/stock integration tests executed.
