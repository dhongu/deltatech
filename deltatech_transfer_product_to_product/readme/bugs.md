# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## PRODUCTTRANSFER-001 — P1: Backorder confirmation is discarded and the replacement can complete alone

- **Status:** Fixed in 19.0.0.0.4. `action_confirm` validates only the source leg and returns its result, so the native `stock.backorder.confirmation` wizard reaches the user. The replacement leg is passed in context and validated from `stock.picking._action_done` after the source leg is done, for the executed quantity (UoM converted), mirroring the decision: native backorder on the replacement for "Create Backorder" / `always`, none for "No Backorder" / `never`. Discarding the confirmation leaves both legs pending. Covered by `tests/test_transfer_product_to_product.py` (fully available, partial with and without backorder, `never` policy).
- **Location:** wizard/transfer_product_to_product_wizard.py, action_confirm().
- **Trigger:** Replace quantity 5 with only part of the source quantity reservable, using an operation type configured to ask about backorders.
- **Actual behavior:** The source button_validate returns a backorder confirmation action without completing that picking. The wizard ignores the action and proceeds to validate the target inventory-to-internal picking. It returns None instead of the pending confirmation.
- **Impact:** Replacement stock can be introduced while the original stock has not been removed. The user is not given the source backorder decision, so the two legs no longer form a completed replacement.
- **Evidence:** Core stock_picking.py button_validate and _pre_action_done_hook explicitly return the action before _action_done. Executed the actual AST-extracted action_confirm method with the first picking returning that action and the second completing: resulting states were confirmed and done, with a None wizard result. Reproduction: audit_coverage/reproductions/product_transfer_validation.py. Synthetic ORM responses confirm control flow; no database stock movement was executed.
- **Suggested fix:** Define a coordinated two-leg workflow; propagate pending actions and do not execute the target leg until the source completion and quantity are verified. Handle partial quantities explicitly.
- **Validation needed:** Fully available, partly available and tracked products; ask/always/never backorder policies; cancellation and retry. Assert matched completed quantities on both legs.

## PRODUCTTRANSFER-002 — P2: Manual reservation makes the wizard validate a zero-quantity source

- **Status:** Open.
- **Location:** wizard/transfer_product_to_product_wizard.py, action_confirm().
- **Trigger:** Use an internal operation type with manual reservation and a storable, untracked source product in an internal location, even with sufficient available stock.
- **Actual behavior:** The wizard creates demand but supplies no executed quantity, confirms both pickings, and never calls action_assign. Confirmation does not reserve ordinary internal moves under manual reservation. Core validation fills quantity from demand only for pickings still draft; these pickings are already confirmed. The zero-quantity sanity check then raises UserError.
- **Impact:** The advertised replacement fails for this supported operation-type configuration.
- **Evidence:** Source comparison with stock_move.py _action_confirm/_should_assign_at_confirm and stock_picking.py button_validate/_sanity_check. No database reproduction of the reservation policy.
- **Suggested fix:** Explicitly prepare/reserve and verify the source quantity before validation; handle unavailable stock and tracked products through the coordinated workflow rather than relying on confirmation to reserve.
- **Validation needed:** Manual, at-confirm and by-date reservation settings with sufficient, partial and absent stock.

## Review limitations

Full eligible module source and its security CSV were inspected. The first finding has an isolated actual-method reproduction; the second follows the local core contracts. No integration tests, valuation postings or production operations were run. No fixes applied.
