# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## FASTPUR-001 — P2: The sent-RFQ fast action skips confirmation and reaches zero-quantity billing

- **Status:** Open; reviewed 2026-10-03.
- **Location:** models/purchase.py, action_button_confirm_to_invoice(); views/purchase_view.xml.
- **Trigger:** Use Confirm, Receipt and Bill on a request for quotation in state sent.
- **Actual behavior:** The view displays the action for draft and sent, but the method calls button_confirm only for draft. The sent order therefore has no confirmed receipt and native purchase-line qty_to_invoice is zero. The local native action_create_invoice builds invoice lines without an invoice-status guard, so source predicts a zero-quantity bill while the order stays sent.
- **Impact:** The advertised combined action does not confirm or receive the order and can create a bill with zero quantities.
- **Evidence:** Executed the actual fast action with a synthetic sent order: confirmation was never called and billing was reached while state remained sent. Traced current local purchase.line qty_to_invoice and purchase.order.action_create_invoice. Zero-quantity account.move creation itself was not executed.
- **Suggested fix:** Handle both supported RFQ states through confirmation, verify successful approval and reception before invoicing, and stop when the expected transition has not completed.
- **Validation needed:** Draft/sent/approval-required orders, ordered versus received billing policies and resulting receipt/bill quantities.

### Additional review limitations — 2026-10-03

Integrated source review traced receipt/refund/replenishment and fast-purchase callers through current native Odoo contracts. Isolated actual-method checks: audit_coverage/reproductions/purchase_return_contracts.py. Database stock/valuation/accounting workflows were not executed; no fixes applied. The refund helper balance overwrite remains an unconfirmed candidate because native tax synchronization may repair it. Fast Purchase and Invoice Receipt define independent non-super receipt_to_stock implementations, so their combined method resolution requires an installed-module integration check.
