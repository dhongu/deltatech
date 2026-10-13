# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEPURCHASE-001 — P2: Cancelling one sale deletes purchase lines shared with other sales

- **Status:** Fixed in 19.0.1.0.2. `_action_cancel()` now unlinks a draft purchase line only when
  none of its non-cancelled destination moves belong to another sale order. On a shared line the
  cancelled moves are detached and their quantity, converted to the line unit of measure, is
  subtracted; the other sale keeps its make-to-order move. Confirmed purchase orders are still left
  untouched. Covered by `test_cancel_keeps_purchase_line_shared_with_other_sale`,
  `test_cancel_shared_purchase_line_converts_uom` and `test_cancel_keeps_shared_confirmed_purchase_line`.
- **Priority:** lowered from P1 to P2 (verification of 2026-10-01). With the default vendor grouping
  `On Order` (`group_rfq = 'default'`), `stock.rule._make_po_get_domain` filters draft RFQs on the
  sale order `reference_ids`, so make-to-order needs of different sales never share a line. The
  defect only occurs for vendors grouping Daily, Weekly or Always.
- **Location:** models/sale_order.py, _action_cancel().
- **Trigger:** Vendor with RFQ grouping Daily/Weekly/Always. Two make-to-order sales for the same product/vendor are consolidated into one draft purchase order line (for example 5 units for sale A and 7 for sale B). Cancel sale A.
- **Actual behavior:** The override unlinks every draft created_purchase_line_ids linked to A, without checking whether the line also supplies B and without subtracting only A demand. Core purchase_stock merges procurement quantities and adds multiple destination moves to the same purchase line.
- **Evidence:** Executed the actual cancellation override with a 12-unit draft purchase line linked to both sale destinations: it deleted that shared line. Inspected purchase_stock._update_purchase_order_line(), which sums quantities and appends destination moves, and its unlink handling. The isolated execution demonstrates the deletion decision; full procurement propagation was not database-tested.
- **Impact:** The still-active sale B loses its ordered supply. Depending on propagate_cancel, its destination move can also be cancelled or switched to make-to-stock by purchase-line unlink.
- **Suggested fix:** Delete only purchase lines exclusively serving cancelled demand. For shared lines, detach cancelled destination moves and recompute the remaining purchase quantity while preserving other sales and accounting/procurement constraints.
- **Validation needed:** Two sales sharing one draft purchase line, cancelling each independently, exclusive lines, sent/confirmed purchases, both propagate_cancel settings, and unit conversion.

## Review limitations

Findings were based on local source inspection; SALEPURCHASE-001 was then reproduced and fixed with database-backed tests (2026-10-01). Not covered by tests: the `propagate_cancel = False` variant of the exclusive-line path, whose behaviour is unchanged.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **SALEPURCHASE-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
