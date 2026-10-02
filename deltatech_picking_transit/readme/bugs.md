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
