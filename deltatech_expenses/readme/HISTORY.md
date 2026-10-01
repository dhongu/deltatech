# Changelog

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
