# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## TRANSIT-001 — P1: Second-leg transfers use a removed stock field

- **Status:** Fixed in 19.0.0.0.11. `stock.picking.create()` no longer receives `move_ids_without_package`; move copying and source-transfer validation read `move_ids`. Covered by `tests/test_picking_transit.py` (wizard creation, automatic creation, validation of the receiving leg, rejection of a product not in the source transfer).
- **Location:** `models/stock_picking.py`, lines 39, 59, and 147–148.
- **Trigger:** Create the second transfer through the wizard or automatic validation; alternatively, validate a transfer linked to a source transfer.
- **Actual behavior:** Creation passes `move_ids_without_package` to `stock.picking.create()`, and subsequent code reads the same removed field.
- **Expected behavior:** Second-leg transfers are created and validated with their stock moves.
- **Impact:** Creation fails with an invalid-field error; source-transfer validation can fail with an attribute error.
- **Evidence:** Odoo 19 declares `stock.picking.move_ids`, but not `move_ids_without_package`. No replacement declaration was found in the custom addons or Enterprise trees.
- **Suggested fix:** Migrate creation, copying, and source-transfer validation to `move_ids`, preserving the intended move selection.
- **Validation needed:** Manual and automatic second-leg creation, then validation of the linked receiving transfer.

## TRANSIT-002 — P2: Computed fields fail on multi-record sets

- **Status:** Fixed in 19.0.0.0.11. Both computes read the current `record` instead of `self`; `_compute_is_transit_transfer` uses `continue` instead of `return`, so later records still get a value. `create_second_transfer_wizard` marks only the processed picking.
- **Location:** `models/stock_picking.py`, `_compute_sub_location_existent` and `_compute_is_transit_transfer`.
- **Trigger:** Read `is_transit_transfer` or `sub_location_existent` on more than one picking (list view, batch processing).
- **Actual behavior:** `Expected singleton` error.
- **Expected behavior:** Each picking gets its own value.
- **Impact:** List and batch operations on transit pickings fail.
- **Validation:** `test_computes_on_multiple_records`.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. The original review ran no database-backed tests. The fixes above were validated with database-backed tests on 2026-10-01.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **TRANSIT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## TRANSIT-003 — P2: Reading the transit indicator toggles the transfer lock

- **Status:** Open; reviewed 2026-10-03.
- **Location:** models/stock_picking.py, _compute_is_transit_transfer().
- **Trigger:** Read or invalidate is_transit_transfer on an internal delivery-type picking without a second transfer. This field is included in the picking form.
- **Actual behavior:** The compute calls action_toggle_is_locked on each eligible record. Native stock.picking implements this as is_locked = not is_locked. Recomputing reverses the flag again, even though the picking data did not change.
- **Impact:** Loading a computed display flag can unlock a protected picking or lock an editable one; the result depends on how often the field is recomputed.
- **Evidence:** Executed the actual AST-extracted compute on a synthetic locked picking: first execution unlocked it; second locked it again. Compared native action_toggle_is_locked. Reproduction: audit_coverage/reproductions/transit_read_lock.py. No browser or ORM cache integration test.
- **Suggested fix:** Keep the indicator compute free of writes to unrelated state. If a workflow must unlock a transfer, use an explicit idempotent action with the appropriate transition and access checks.
- **Validation needed:** Repeated form/list reads and cache invalidation, originally locked/unlocked records, completed pickings and batch reads; assert the lock remains unchanged by indicator reads.

## TRANSIT-004 — P1: Partial delivery backorders orphan products in the receiving leg

- **Status:** Open; reviewed 2026-10-03.
- **Location:** models/stock_picking.py, button_validate(), create_second_transfer_wizard(), copy_move_lines(); native stock.picking._create_backorder().
- **Trigger:** Automatically generate the reception for a delivery containing products A and B. Deliver A but leave B wholly unprocessed and choose to create a backorder.
- **Actual behavior:** The addon creates the reception with both products before native delivery validation. Core backordering moves the unprocessed B move to another source picking. The reception still references the original picking, so its validation rejects B because the original source now contains only A. The source backorder inherits second_transfer_created=True, preventing its automatic creation path from producing a separate reception. Copied moves have no explicit native move_orig_ids/move_dest_ids chain.
- **Impact:** An ordinary partial two-step delivery creates a reception that cannot be completed, and the pending source picking carries an already-created flag that does not describe its own receiving leg. Manual repair is required to complete the remaining flow.
- **Evidence:** Traced the addon override through native button_validate, stock.move backorder splitting and stock.picking._create_backorder_picking/_create_backorder. Both addon linkage fields use the default copy behavior; core backorder copy supplies no reset. Isolated execution of the actual receiving guard with B now absent from the original source raises UserError for B. Actual copy_move_lines execution retains the original demand and supplies no chain link. Reproduction: audit_coverage/reproductions/transit_read_lock.py. Full database backorder creation was not executed.
- **Suggested fix:** Coordinate second-leg creation with completed source moves and source backorders, maintain explicit move/picking links, and define which flag/link belongs to each generated picking. Preserve product, quantity, UoM and lot correspondence across partial shipments.
- **Validation needed:** A delivered/B wholly backordered, partially processed quantities of one product, multiple source backorders, reception backorders and repeated validation. Assert each receiving leg references its actual source and the complete flow remains executable.
