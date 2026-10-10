# Changelog

## 20.0.3.3.4 (2026-10-10)

- **Fix (EXPENSES-001): the workflow and a done deduction are protected on the
  server.** The status could be changed by a direct write (for example over
  RPC) without the role checked by the Advance / Validate / Invalidate buttons,
  and the amounts and lines of a done deduction could still be changed after the
  receipts and journal entries were posted. The status is now changed only by
  the workflow buttons; on a done or cancelled deduction the advance, per diem,
  days, journals, accounts, dates, employee and lines can no longer be changed,
  and a correction is made by invalidating and validating again. A deduction is
  cancelled only by the accountant and only in Draft.
- In the Advance state, once the advance entry is posted, the advance amount,
  the cash and advance journals, the advance date, the employee and the company
  can no longer be changed (the settlement difference was computed against a
  different advance than the posted one: a fictitious refund and a credit
  balance on 542). Lines, days and per diem stay editable; to change the
  advance, invalidate the deduction.

## 20.0.3.3.3 (2026-10-07)

- Apps Store page in English (it was in Romanian), written from the 20.0 code, with
  Configuration and Usage sections, and the Romanian translation in its own tab
  (`readme/*.ro.md`). The test scenario is left out of the page. Summary in English; support
  address.

## 20.0.3.3.2 (2026-10-04)

- **Fix (EXPENSES-002): the expense lines are always in the company currency
  of the deduction.** A line could get another currency (the journal currency,
  the currency of the user's main company, or one sent by an integration such
  as the HR expense import), but its amount was still added to the totals and
  posted as company currency, so the currency shown on the line was wrong.
  The line currency is now derived from the deduction company and a currency
  sent on create/write is ignored; amounts are entered in the company
  currency. The migration (`migrations/20.0.3.3.2`) aligns the currency of
  existing lines; amounts, totals and posted entries do not change. Port of
  19.0.3.4.1 (dhongu/deltatech#3117). The 19.0.3.4.0 changes (gross line
  amount, settlement date, supplier advance 4092) are not part of this port.

## 20.0.3.3.1 (2026-10-01)

- Migration to Odoo 20.0: access rights and record rules moved to
  `security/ir.access.csv` (same roles and restrictions: own deductions for
  Employee, full access for Approver/Accountant, multi-company on deductions
  and lines); report uses `t-out`; journal entries unchanged from 19.0
  (covered by a full Dr/Cr scenario test).

## 19.0.3.3.1 (2026-09-25)

- Fix: the "Expenses Deductions" smart button on the employee form had no
  group restriction, so any internal user without an expenses group got an
  access error on `deltatech.expenses.deduction` when opening an employee
  (e.g. a Time Off officer). The button is now shown only to the expenses
  groups (Employee, Approver, Accounting).
