# Bug review — deltatech_invoice_to_draft

Review date: 2026-10-02. Target version: Odoo 19.

## DRAFTACCESS-001 — P1: Reset-to-draft permission is enforced only through button visibility

- **Status:** Fixed in 19.0.2.0.3. `button_draft` checks the group when it is called remotely (web
  client, XML-RPC/JSON-RPC, `/json/2`), including through `button_cancel` on a posted move; the
  *Cancel Entry* shortcut always requires the group and is hidden without it. Superuser and server-side
  flows that reset a move internally (payment reset/cancel, unlink, bank reconciliation, POS) are not blocked.
- **Location:** models/account_move.py; views/account_move_view.xml.
- **Trigger:** A user without Can reset account move to draft invokes button_draft by RPC, or clicks the added Cancel Entry button while allowed by native accounting access.
- **Actual behavior / impact:** The module only masks show_reset_to_draft_button and never checks its group server-side. Its added button_draft_cancel explicitly calls button_draft before cancellation and is visible to account.group_account_invoice without the custom group. Native button_draft enforces accounting restrictions but does not check this addon group.
- **Evidence:** Complete addon and native button_draft inspected. The added action calls the reset path regardless of the custom group; no application/database mutation executed.
- **Suggested fix:** Enforce the custom permission in the reset action server-side, and align the cancel-entry button with that policy.
- **Validation needed:** Users with/without the custom group, direct RPC, posted-entry Cancel Entry, native lock/cancellation-request restrictions.

## Review limitations

All eligible source read. Native methods compared; kit selection executed only with mocked records. No Odoo access, invoice or sale integration tests executed.
