# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## TRANSIT-001 — P1: Second-leg transfers use a removed stock field

- **Status:** Open.
- **Location:** `models/stock_picking.py`, lines 39, 59, and 147–148.
- **Trigger:** Create the second transfer through the wizard or automatic validation; alternatively, validate a transfer linked to a source transfer.
- **Actual behavior:** Creation passes `move_ids_without_package` to `stock.picking.create()`, and subsequent code reads the same removed field.
- **Expected behavior:** Second-leg transfers are created and validated with their stock moves.
- **Impact:** Creation fails with an invalid-field error; source-transfer validation can fail with an attribute error.
- **Evidence:** Odoo 19 declares `stock.picking.move_ids`, but not `move_ids_without_package`. No replacement declaration was found in the custom addons or Enterprise trees.
- **Suggested fix:** Migrate creation, copying, and source-transfer validation to `move_ids`, preserving the intended move selection.
- **Validation needed:** Manual and automatic second-leg creation, then validation of the linked receiving transfer.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. No database-backed integration tests were run. No fixes have been applied.
