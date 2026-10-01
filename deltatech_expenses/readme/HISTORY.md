# Changelog

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
