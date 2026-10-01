# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEPURCHASE-001 — P1: Cancelling one sale deletes purchase lines shared with other sales

- **Status:** Open.
- **Location:** models/sale_order.py, _action_cancel().
- **Trigger:** Two make-to-order sales for the same product/vendor are consolidated into one draft purchase order line (for example 5 units for sale A and 7 for sale B). Cancel sale A.
- **Actual behavior:** The override unlinks every draft created_purchase_line_ids linked to A, without checking whether the line also supplies B and without subtracting only A demand. Core purchase_stock merges procurement quantities and adds multiple destination moves to the same purchase line.
- **Evidence:** Executed the actual cancellation override with a 12-unit draft purchase line linked to both sale destinations: it deleted that shared line. Inspected purchase_stock._update_purchase_order_line(), which sums quantities and appends destination moves, and its unlink handling. The isolated execution demonstrates the deletion decision; full procurement propagation was not database-tested.
- **Impact:** The still-active sale B loses its ordered supply. Depending on propagate_cancel, its destination move can also be cancelled or switched to make-to-stock by purchase-line unlink.
- **Suggested fix:** Delete only purchase lines exclusively serving cancelled demand. For shared lines, detach cancelled destination moves and recompute the remaining purchase quantity while preserving other sales and accounting/procurement constraints.
- **Validation needed:** Two sales sharing one draft purchase line, cancelling each independently, exclusive lines, sent/confirmed purchases, both propagate_cancel settings, and unit conversion.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
