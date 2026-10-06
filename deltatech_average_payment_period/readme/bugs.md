# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## AVGPAY-001 — P2: Stored payment dates and durations are not cleared when reconciliation is absent

- **Status:** Open.
- **Location:** models/account.py, _compute_payment_days(), _compute_payment_days_simple().
- **Trigger:** Recompute a previously paid invoice journal item after removing its full reconciliation.
- **Actual behavior:** Neither compute resets its fields outside the reconciled branches. The main compute continues using the old payment_date, and the simple duration retains its old value.
- **Impact:** Unreconciled journal items can continue displaying a payment date and paid duration. Other consumers of the stored fields can mistake stale values for current payment history. The SQL average report itself excludes items without full_reconcile_id, so this finding does not claim they remain in that report after unreconciliation.
- **Evidence:** Executed both actual AST-extracted computes with full_reconcile_id=False and previously stored date/durations: payment date January 11 and both ten-day durations remained. Linked counterpart dates are also missing from dependency declarations. No ORM recomputation or flush/reload executed.
- **Suggested fix:** Assign defaults on every compute path and declare mutable inputs used to derive the payment date, including relevant counterpart dates and accounting classification.
- **Validation needed:** Paid/unpaid transitions, reconciliation removal/recreation, counterpart date edits, noninvoice lines and flush/reload.

## AVGPAY-002 — P1: The SQL payment-history report bypasses company isolation

- **Status:** Open.
- **Location:** report/account_average_payment.py; security/ir.model.access.csv; manifest security data.
- **Trigger:** An accounting user restricted to company A queries account.average.payment.report while posted fully reconciled invoices exist in company B.
- **Actual behavior:** The SQL view selects journal items from every company. The independent report model has no company rule; its read ACL permits account users. Parent account.move and account.move.line rules are not automatically applied to a separate SQL-view model.
- **Impact:** Invoice identities, partner payment history and debit/credit amounts from unauthorized companies can be disclosed through report search or grouping.
- **Evidence:** Full view SQL, fields, ACL and manifest inspected; no report rule found in the local XML trees. The forecast caller explicitly filters history by invoice company, which protects that caller but does not secure direct report access. Partner-rating also consumes this report without adding a company predicate in its payment-time helper. No database access test executed.
- **Suggested fix:** Enforce allowed-company scope on the report through a record rule using move_id.company_id or a stored/view company field; review downstream rating and reporting domains.
- **Validation needed:** Direct read/search/read_group with one allowed company, two allowed companies and a company switch; ensure unrelated company data remains inaccessible.

## Review limitations

Full eligible module source read and native contracts/dependent forecast and rating callers inspected. Executable isolated checks: audit_coverage/reproductions/payment_terms_history.py. These checks do not establish database lifecycle or access enforcement. No production operations or fixes applied.
