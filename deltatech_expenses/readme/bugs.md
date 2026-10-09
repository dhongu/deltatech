# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## EXPENSES-001 — P1: Direct writes bypass workflow roles and alter finalized deductions

- **Status:** Fixed in 19.0.3.5.2 — `state`, `approved_by_id`, `accounted_by_id` and `move_id` are written only by the workflow methods (which check the same groups as the buttons and then write as superuser); a direct `write`/`create` by a user is refused. On a done or cancelled deduction, `write` refuses the fields that make up the amounts and the journal entries (`_get_locked_fields()`: advance, days, per diem, journals, accounts, dates, employee, lines, receipts, payments), and the lines cannot be created, changed or deleted; corrections go through Invalidate. `cancel_expenses` requires the Accounting role and the Draft state. Superuser/`sudo()` is not blocked. Covered by `test_user_without_role_cannot_write_state`, `test_finalized_deduction_is_locked_for_accountant` and `test_superuser_and_cancel_draft_not_blocked` in `tests/test_expenses.py`.
- **Location:** models/deltatech_expenses_deduction.py; security/ir.model.access.csv.
- **Trigger:** An Expenses Employee writes state or an expense line through ORM/RPC, including on their own finalized deduction.
- **Actual behavior:** Employee has write permission on both models. The role checks protect named validation/invalidation methods, but there is no write override or field group restriction enforcing the state/role invariant. State readonly is a UI property. Lines also have no finalized-state write guard. cancel_expenses directly writes cancel without a role or current-state check.
- **Evidence:** Complete deduction/line model and ACL source inspected. Own-record rules restrict which deduction is accessible but do not restrict writable fields or finalized states. No live RPC/database write executed.
- **Impact:** Employees can mark documents done/advance without the corresponding bookkeeping, cancel accounted documents while leaving posted entries, or change recorded amounts after posting, breaking consistency between the deduction and ledger.
- **Suggested fix:** Enforce workflow transitions and final-state immutability on the server, while permitting the validated accounting paths and explicitly authorized corrections.
- **Validation needed:** Employee direct writes to state, advance, lines and finalized documents must be rejected; normal approver/accounting workflows must remain valid.

## EXPENSES-002 — P1: Line currency is ignored in totals and accounting

- **Status:** Fixed in 19.0.3.4.1 — the line `currency_id` is a stored compute from `expenses_deduction_id.company_id.currency_id` (the deduction is kept and posted in company currency), a `currency_id` sent on create/write is dropped, and the migration `migrations/19.0.3.4.1/post-migration.py` aligns existing lines (amounts unchanged). Covered by tests in `tests/test_expenses.py` (`test_line_currency_is_company_currency`, `test_line_currency_follows_deduction_company`).
- **Location:** models/deltatech_expenses_deduction.py, line.currency_id, `_get_currency()`, `_compute_amount()` and `validate_expenses()`.
- **Trigger:** A line currency differs from the deduction company's currency, including a programmatically created line or a multi-company default taken from env.user.company_id.
- **Actual behavior:** The line has an independent required currency and defaults to journal currency or the user's main-company currency. The deduction currency is its company currency. Totals add line price_subtotal/tax_amount directly, and accounting writes those same numeric amounts into company-currency debit/credit or receipt price_unit without conversion or a currency consistency constraint.
- **Evidence:** Full line computation, parent totals, receipt and settlement dictionaries inspected: no _convert or requirement that line currency equal parent currency. A line amount of 100 EUR is numerically treated as 100 RON by a RON-company deduction. No exchange-rate or posting test executed.
- **Impact:** Foreign-currency lines or incorrect multi-company defaults produce misstated totals, advance differences and accounting entries.
- **Suggested fix:** Either enforce and derive the company currency on all lines or implement dated conversion and foreign-currency accounting explicitly.
- **Validation needed:** Different line/company currencies and a user's main company different from the deduction company; verify defaults, totals and posted values.

## EXPENSES-003 — P2: Partner-to-employee migration ignores deduction company

- **Status:** Open.
- **Location:** migrations/19.0.3.0.0/post-migration.py, employee search/create and deduction UPDATE.
- **Trigger:** Upgrade legacy deductions belonging to different companies that share one work contact, or migrate a shared contact with no existing employee.
- **Actual behavior:** Migration selects distinct partners without company, searches one employee by work_contact_id only, and updates every deduction for that partner with the same employee. Employee creation uses the partner company or migration environment company rather than the deduction company.
- **Evidence:** Source inspected in full. Executed the exact UPDATE string extracted by AST in an isolated SQLite example: deductions in companies 10 and 20 with partner 42 both receive employee 100, even when that employee belongs to company 10. No Odoo migration/database upgrade executed.
- **Impact:** Company-specific employee attribution is lost, and deductions may become associated with an employee from another company. Employee-based ownership rules and accounting partner attribution then use the wrong employee association.
- **Suggested fix:** Map by deduction company and original partner, search/create the employee within that company, and restrict each UPDATE to that company. Handle shared contacts explicitly.
- **Validation needed:** Upgrade two companies sharing a contact with separate employees, and shared-contact deductions without existing employees; verify employee company and ownership after migration.

## Review limitations

All eligible module Python and XML source files have been manually reviewed. No database posting, accounting reversal or integration tests executed in this pass.
