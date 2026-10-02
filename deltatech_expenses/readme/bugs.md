# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## EXPENSES-001 — P1: Direct writes bypass workflow roles and alter finalized deductions

- **Status:** Open.
- **Location:** models/deltatech_expenses_deduction.py; security/ir.model.access.csv.
- **Trigger:** An Expenses Employee writes state or an expense line through ORM/RPC, including on their own finalized deduction.
- **Actual behavior:** Employee has write permission on both models. The role checks protect named validation/invalidation methods, but there is no write override or field group restriction enforcing the state/role invariant. State readonly is a UI property. Lines also have no finalized-state write guard. cancel_expenses directly writes cancel without a role or current-state check.
- **Evidence:** Complete deduction/line model and ACL source inspected. Own-record rules restrict which deduction is accessible but do not restrict writable fields or finalized states. No live RPC/database write executed.
- **Impact:** Employees can mark documents done/advance without the corresponding bookkeeping, cancel accounted documents while leaving posted entries, or change recorded amounts after posting, breaking consistency between the deduction and ledger.
- **Suggested fix:** Enforce workflow transitions and final-state immutability on the server, while permitting the validated accounting paths and explicitly authorized corrections.
- **Validation needed:** Employee direct writes to state, advance, lines and finalized documents must be rejected; normal approver/accounting workflows must remain valid.

## EXPENSES-002 — P1: Line currency is ignored in totals and accounting

- **Status:** Open.
- **Location:** models/deltatech_expenses_deduction.py, line.currency_id, `_get_currency()`, `_compute_amount()` and `validate_expenses()`.
- **Trigger:** A line currency differs from the deduction company's currency, including a programmatically created line or a multi-company default taken from env.user.company_id.
- **Actual behavior:** The line has an independent required currency and defaults to journal currency or the user's main-company currency. The deduction currency is its company currency. Totals add line price_subtotal/tax_amount directly, and accounting writes those same numeric amounts into company-currency debit/credit or receipt price_unit without conversion or a currency consistency constraint.
- **Evidence:** Full line computation, parent totals, receipt and settlement dictionaries inspected: no _convert or requirement that line currency equal parent currency. A line amount of 100 EUR is numerically treated as 100 RON by a RON-company deduction. No exchange-rate or posting test executed.
- **Impact:** Foreign-currency lines or incorrect multi-company defaults produce misstated totals, advance differences and accounting entries.
- **Suggested fix:** Either enforce and derive the company currency on all lines or implement dated conversion and foreign-currency accounting explicitly.
- **Validation needed:** Different line/company currencies and a user's main company different from the deduction company; verify defaults, totals and posted values.

## Review limitations

Module source review remains in progress. No database posting, accounting reversal or integration tests executed in this pass.
