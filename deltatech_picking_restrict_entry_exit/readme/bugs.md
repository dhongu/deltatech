# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RESTRICT-001 — P2: Save-time move restrictions are bypassed by the Odoo 19 field

- **Status:** Fixed in 19.0.0.0.13 / 20.0.0.0.13 — `write()` now checks the `move_ids` commands (CREATE and UPDATE, tuple or
  list form, virtual or `0` id for new lines); covered by `tests/test_picking_restrict.py`, including end-to-end
  `Form` saves without mocking the base write.
- **Location:** `models/stock_picking.py:95–192, write()`.
- **Trigger:** Save a picking with updated done quantities or additional moves through the current move_ids relation.
- **Actual behavior / impact:** The override checks only move_ids_without_package, removed in Odoo 19. Current move_ids commands bypass all save-time checks. A quantity above demand can therefore be saved; button_validate still has separate checks and may reject it later.
- **Evidence:** Executed the actual extracted write override with move_ids and a quantity update: it called the base writer without querying any restriction. Local stock.picking declares move_ids, not move_ids_without_package.
- **Suggested fix:** Handle current move_ids commands and supported command forms, or enforce the policy at stock.move writes consistently with validation exemptions.
- **Validation needed:** For a restricted user, attempt to save excess done quantity and a manual incoming/outgoing move; also check legitimate returns and same-warehouse internal transfers.

## Review limitations

Source inspection and isolated executions with mocked records; no database-backed module installation or integration tests were run in this pass.
