# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## INVENTORY-001 — P1: Inventory is finalized before the conflict wizard resolves stock changes

- **Status:** Fixed in 19.0.2.10.2. `action_apply_inventory()` now returns the `stock.inventory.conflict` action untouched when the core asks for conflict resolution: the inventory stays *In progress*, lines are not marked OK, and the quant keeps its inventory/line links, note and last inventory date. When the wizard is resolved (keep counted quantity or keep difference), the same document is finalized and the inventory move carries the note. Covered by `tests/test_inventory_conflict.py` (cancelled wizard, both resolutions, adjustment without conflict). Priority P1 confirmed.
- **Location:** models/stock_quant.py, action_apply_inventory(), lines 65–100; Odoo stock/models/stock_quant.py, action_apply_inventory().
- **Trigger:** Count a quant, allow an intervening stock movement so is_outdated becomes true, then apply the count.
- **Actual behavior:** The superclass returns the stock.inventory.conflict wizard before applying stock moves. The override still marks lines is_ok, sets the inventory state to done, updates last_inventory_date, and clears inventory links and inventory_note. Closing or cancelling the wizard leaves a completed inventory document without its stock adjustment.
- **Evidence:** Executed the actual override against a superclass returning the standard conflict action. Stock quantity stayed 10, while inventory state became done, the line became is_ok, and inventory links and note were cleared. Verified that the local core implementation returns the wizard before calling _apply_inventory().
- **Impact:** Inventory documents falsely certify unapplied counts; resolving the wizard later can create a separate inventory document because the original links were removed.
- **Suggested fix:** Defer all completion and cleanup until stock application actually succeeds; propagate wizard actions without marking the inventory done, and preserve document links through conflict resolution.
- **Validation needed:** An outdated quant followed by cancelling the wizard, accepting the count, keeping updated stock, and a normal adjustment without conflicts; verify document, move, and note linkage.

## Review limitations

Findings were based on local source inspection and isolated reproductions. INVENTORY-001 was then reproduced and fixed with database-backed tests (2026-10-01).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **INVENTORY-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
