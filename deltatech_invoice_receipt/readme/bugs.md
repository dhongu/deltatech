# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RECEIPT-001 — P1: Automatic receipt deletes moves that already have a quantity

- **Status:** Fixed in 19.0.2.0.2. `receipt_to_stock()` no longer unlinks any move: every move with a positive demand gets its quantity set to the demand and is marked `picked`, so `_action_done` validates it; zero-demand moves are left to `_action_done`, which cancels them. Tests now assert the receipt state, the received quantity on the purchase line and the stock on hand (standard flow, partially entered quantity, zero quantity, 2-step reception, invoice posting).
- **Priority re-evaluated:** P1 confirmed, impact larger than first described (verification 2026-10-01). In Odoo 19 supplier receipts bypass reservation and `_action_assign` sets the full quantity at confirmation, so in the standard flow *every* receipt move had `quantity == demand` and was deleted on `action_post` of the vendor bill: nothing was received. Even the kept branch was broken, because the moves were not marked `picked` and stayed `assigned`. Where a receipt move is chained to a later operation (`move_dest_ids`), `unlink` raised a UserError and blocked posting the bill.
- **Location:** `models/purchase.py`, `receipt_to_stock()`, lines 34–38.
- **Trigger:** Run automatic receipt on an assigned picking whose stock moves already have a reserved or entered quantity.
- **Actual behavior:** The method only keeps moves with a positive demand and zero `quantity`. Every other move is unlinked, including a legitimate move with demand 5 and quantity 5.
- **Example:** Isolated execution deleted a 5-unit assigned move before calling picking validation.
- **Impact:** Expected receipt lines can disappear, so products are not received as intended.
- **Evidence:** Executed the existing method with a mocked assigned picking. In Odoo 19, move quantity is computed from stock move line quantities, including assigned quantities. The current module test does not assert the resulting stock quantity.
- **Suggested fix:** Retain valid positive-demand moves, preserve or deliberately adjust existing quantities, and handle zero-demand lines separately.
- **Validation needed:** Automatic receipt with zero, fully reserved, partially entered, and fully entered quantities; assert actual received stock.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. RECEIPT-001 was fixed on 2026-10-01 with database-backed tests (`tests/test_receipt.py`).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **RECEIPT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
