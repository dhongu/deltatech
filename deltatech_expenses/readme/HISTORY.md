# Changelog

## 19.0.3.4.1 (2026-10-03)

- **Fix (EXPENSES-002): the expense lines are always in the company currency
  of the deduction.** A line could get another currency (the journal currency,
  the currency of the user's main company, or one sent by an integration such
  as the HR expense import), but its amount was still added to the totals and
  posted as company currency, so the currency shown on the line was wrong.
  The line currency is now derived from the deduction company and a currency
  sent on create/write is ignored; amounts are entered in the company
  currency. The migration aligns the currency of existing lines; amounts,
  totals and posted entries do not change.

## 19.0.3.4.0 (2026-10-01)

- The line amount is now always the receipt total, VAT included, whatever the
  tax configuration. Before, with the standard Romanian purchase taxes (VAT
  on top of the price), VAT was added over the amount, so typing the receipt
  total inflated the expense, the deductible VAT and the amount owed to the
  employee. The migration turns the amount of existing lines into their
  previous gross (base + VAT), so their base and VAT do not change.
- The cash entry that settles the advance difference (refund or extra
  payment) is dated on the expense date, not on the advance date.
- A direct supplier payment from the advance that no open bill covers is a
  supplier advance: the remainder is reclassified Dr 4092 = Cr 401 and
  reconciled, so no debit balance is left on 401.
- Tax columns and a "Vouchers" tab on the deduction form; the "Payments" tab
  is shown only when it has payments. Romanian labels fixed ("Alte
  informații", "Total chitanțe", "Diferență avans", "Cont diurnă", journals).
- Consultant sheet and screenshots updated; the screenshot test is back in
  this module and runs without `hr_expense`.

## 19.0.3.3.1 (2026-09-25)

- Fix: the "Expenses Deductions" smart button on the employee form had no
  group restriction, so any internal user without an expenses group got an
  access error on `deltatech.expenses.deduction` when opening an employee
  (e.g. a Time Off officer). The button is now shown only to the expenses
  groups (Employee, Approver, Accounting).
