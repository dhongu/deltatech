# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## INVENTORY-001 — P1: Inventory is finalized before the conflict wizard resolves stock changes

- **Status:** Open.
- **Location:** models/stock_quant.py, action_apply_inventory(), lines 65–100; Odoo stock/models/stock_quant.py, action_apply_inventory().
- **Trigger:** Count a quant, allow an intervening stock movement so is_outdated becomes true, then apply the count.
- **Actual behavior:** The superclass returns the stock.inventory.conflict wizard before applying stock moves. The override still marks lines is_ok, sets the inventory state to done, updates last_inventory_date, and clears inventory links and inventory_note. Closing or cancelling the wizard leaves a completed inventory document without its stock adjustment.
- **Evidence:** Executed the actual override against a superclass returning the standard conflict action. Stock quantity stayed 10, while inventory state became done, the line became is_ok, and inventory links and note were cleared. Verified that the local core implementation returns the wizard before calling _apply_inventory().
- **Impact:** Inventory documents falsely certify unapplied counts; resolving the wizard later can create a separate inventory document because the original links were removed.
- **Suggested fix:** Defer all completion and cleanup until stock application actually succeeds; propagate wizard actions without marking the inventory done, and preserve document links through conflict resolution.
- **Validation needed:** An outdated quant followed by cancelling the wizard, accepting the count, keeping updated stock, and a normal adjustment without conflicts; verify document, move, and note linkage.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
