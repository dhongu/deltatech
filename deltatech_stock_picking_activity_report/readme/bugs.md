# Bug review — deltatech_stock_picking_activity_report

Review date: 2026-10-02. Target version: Odoo 19.

## PICKACT-001 — P1: Stock users can read and alter journals outside picking company scope

- **Status:** Fixed in 19.0.1.1.3 — `company_id` (related `picking_id.company_id`, stored) on the journal, new `security/security.xml` with a multi-company rule, and the ACL reduced to read-only for `stock.group_stock_user` (full rights only for `base.group_system`); logging keeps writing through `sudo()`. Covered by tests in `tests/test_company_access.py`.
- **Location:** security/ir.model.access.csv; models/stock_picking_activity_record.py.
- **Trigger:** A stock user accesses the journal model directly through ORM/RPC.
- **Actual behavior:** stock.group_stock_user has full CRUD without company/picking/owner rules. The independent model stores global sudo-written logs and arbitrary user_id, and no parent authorization or immutability guard applies.
- **Evidence:** Full model, ACL, manifest and views read. No security rules are loaded; activity_log readonly and list create=false only affect UI. No real log records accessed.
- **Impact:** Users can read logged operations from inaccessible companies and forge/delete history or attribute events to other users.
- **Suggested fix:** Apply explicit picking/company read scope and restrict log mutations to controlled logging/admin paths.
- **Validation needed:** Two companies, restricted pickings, direct read/create/write/unlink and forged user_id; journal permissions must follow intended scope.

## PICKACT-002 — P2: Batch validation overwrites every journal with each picking quantity

- **Status:** Open.
- **Location:** models/stock_picking.py, button_validate().
- **Trigger:** Validate two or more pickings together, with different quantities or operation directions.
- **Actual behavior:** Inside for picking in self, the method logs on self.with_context rather than picking.with_context. Each picking-specific quantity/context is therefore applied to every picking in the recordset; subsequent iterations overwrite same-direction values.
- **Evidence:** Actual AST override with outgoing quantities 3 and 7 logs IDs [1,2] twice, first quantity 3 then 7. Mock logging shim only.
- **Impact:** Both journals can end with quantity 7, and mixed-direction batches attribute unrelated entry/exit/internal work to every picking.
- **Suggested fix:** Log on the current singleton picking and calculate counts in an explicit compatible-unit policy.
- **Validation needed:** Two outgoing pickings with differing quantities, reversed order and mixed incoming/outgoing/internal operations.

## PICKACT-003 — P2: Validation is recorded before confirmation wizards complete

- **Status:** Open.
- **Location:** models/stock_picking.py, button_validate().
- **Trigger:** Native validation returns a backorder confirmation action rather than completing the transfer; the user then closes/cancels it.
- **Actual behavior:** After super.button_validate the method unconditionally logs has_validated=True and product quantities, without checking picking.state or whether a wizard remains pending.
- **Evidence:** Actual extracted override with superclass returning stock.backorder.confirmation and assigned pickings still issues validation logs. Compared native validation wizard return flow. No Odoo transfer/wizard execution.
- **Impact:** Validated Count and handled quantities can report work that has not been completed, even when the user abandons the wizard.
- **Suggested fix:** Record completed validation only for pickings that actually reach done; hook the completion path or distinguish attempted/pending validation.
- **Validation needed:** Backorder wizard opened/cancelled/confirmed, already-done pickings and mixed completed/pending batches; count only successful completions.

## Review limitations

All eligible source was read. Reproductions use actual AST-extracted methods with mock location/validation/logging objects. No Odoo stock mutations, database integration tests or live access probes executed.
