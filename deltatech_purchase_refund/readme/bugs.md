# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## PURREFUND-001 — P2: Refund action writes an obsolete default and leaves the bill type unchanged

- **Status:** Open; reviewed 2026-10-03.
- **Location:** models/purchase.py, PurchaseOrder.action_view_invoice().
- **Trigger:** Open the bill action for a purchase order with a negative uninvoiced quantity and create a document from that action.
- **Actual behavior:** The addon sets default_type=in_refund. The native vendor-bill action still contains default_move_type=in_invoice, which is the actual account.move default key.
- **Impact:** New documents opened through the action remain vendor bills instead of the intended vendor credit notes. This finding concerns the action context, not native action_create_invoice automatic negative-total switching.
- **Evidence:** Executed the actual override with the native action context: default_move_type stayed in_invoice while default_type became in_refund. Native vendor-bill action and account.move move_type consumers inspected.
- **Suggested fix:** Set default_move_type consistently and verify existing-invoice versus new-document behavior.
- **Validation needed:** Negative uninvoiced ordered/received quantities, existing bill list and new credit note creation.

### Additional review limitations — 2026-10-03

Integrated source review traced receipt/refund/replenishment and fast-purchase callers through current native Odoo contracts. Isolated actual-method checks: audit_coverage/reproductions/purchase_return_contracts.py. Database stock/valuation/accounting workflows were not executed; no fixes applied. The refund helper balance overwrite remains an unconfirmed candidate because native tax synchronization may repair it. Fast Purchase and Invoice Receipt define independent non-super receipt_to_stock implementations, so their combined method resolution requires an installed-module integration check.
