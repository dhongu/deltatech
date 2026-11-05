# Changelog

## 19.0.3.11.0 (2026-11-05)

- The option **Advance and Settlement via Bank Statement / Cash Register** moves from the company to
  the journal (cash, bank or company card journal, Journal Entries tab). An expense report takes it
  from the journal of its settlement mode (the card journal for Company card, the payment journal
  otherwise), so the same company can settle cash advances on the expense report and company card
  advances through the bank statement. The variant is stored on the expense report: reports in Draft
  follow a change of the journal option, reports in Advance or Done keep their flow, so the option
  no longer needs to be blocked by pending advances.
- Settlement mode and payment / card journal stay visible on the expense reports settled through the
  bank statement or cash register, as they choose the variant.
- Smart button **Balance 542** on the expense report: the balance of the employee on the 542 account
  of the report (in the account currency for a 542 in a foreign currency); it opens the 542 ledger of
  the employee, posted entries with the cumulated balance. Users without accounting read rights see
  the balance as a field, without the link.
- Migration: on a company that had the option, it is set on its cash, bank and card journals, and its
  expense reports keep the variant they were created with.
- Consultant sheet and screenshots updated (journal option, balance button, 542 ledger).

## 19.0.3.10.0 (2026-11-04)

- New company option **Advance and Settlement via Bank Statement / Cash Register** (Invoicing
  settings, Bank & Cash): the
  expense report books only the expenses, always on 542 with the employee as partner (receipts,
  supplier payments, per diem), whatever the settlement mode, company card included. It posts no
  advance, no refund and no extra payment, and no exchange difference on 542: the money handed to
  the employee and the refunds are recorded from the cash register or the bank statement,
  reconciled on 542. The report has no Advance step: it is validated from Draft, gets its number
  then and ends in Done. The form shows the employee balance on 542 instead of the difference.
- The advance date is today by default.
- Search filters **Advance** and **Done** on the expense reports.
- The option cannot be enabled while expense reports of the company are in the Advance state:
  they are finalized first, in the flow with payment entries.
- The money handed to the employee and the refunds are reconciled on 542 with the standard bank
  statement or cash register reconciliation: account 542 must allow reconciliation and the partner is
  the work contact of the employee.
- Consultant sheet: at year end the credit balance of an employee on 542 is reclassified to
  4281 (`Dr 542 = Cr 4281`), as a manual entry.
- Without payment entries, an expense report in a foreign currency is validated only on a 542
  account in that currency (account currency set), so that the monthly revaluation of the
  localization revalues the balance of the employee; a report in the company currency only on a
  542 account without currency. Changing the currency proposes the matching expense journal.
- Consultant sheet: checks and error messages of the variant without payment entries.
- With the option, the status bar of the expense report shows only Draft and Done.
- With the option, the settlement lines on 542 are labelled "Decontare cheltuieli" (no advance).
- The title of a draft expense report is translated.
- Screenshots of the variant via bank statement / cash register in the consultant sheet.

## 19.0.3.9.1 (2026-11-04)

- Fix: the **Expenses Deductions** counter on the employee (`expenses_deduction_count`) is now restricted to HR users (`groups="hr.group_hr_user"`), like the company card journal. It is not on the public employee profile, so users without HR rights (website, POS) got an access error when reading an employee. New test: `test_employee_public_access`.

## 19.0.3.9.0 (2026-11-04)

- A **Supplier Payment** line takes the payable account of the supplier (401), set from the
  partner and read-only; an **Expense** line keeps the default expense account, chosen by the
  accountant.
- A **Supplier Payment** line has no VAT: the taxes cannot be filled in and are ignored, as the
  bill paid already has its VAT booked. The amount paid is the total of the line.

## 19.0.3.8.0 (2026-10-29)

- A supplier payment line can name the bills it pays (button on the line, **Bills Paid**): for
  each bill, the allocated amount (by default its amount due, at most the unallocated part of the
  payment). On validation the entry Dr 401 = Cr 542 has one 401 line per bill, reconciled only with
  that bill, so the bill becomes paid or partially paid and shows the payment with the report
  number. Bills in the currency of the report are settled in that currency; the exchange
  difference goes to 665/765. Invalidating the report undoes the reconciliations.
- The unallocated part of a supplier payment is a supplier advance and is still reclassified
  Dr 4092 = Cr 401, as when no bill covers the payment.
- Without bills named on the line, the payment still settles the oldest open bills first.
- The 401 line of a supplier payment is booked on the supplier company (commercial partner): a
  line entered with a contact person of the supplier did not find the company's bills.

## 19.0.3.7.2 (2026-10-27)

- The company card journal on the employee is restricted to HR officers: users
  without HR rights (e.g. the PoS cashier) got an access error when reading
  employees, as the field was prefetched from the public employee profile.

## 19.0.3.7.1 (2026-10-27)

- A direct supplier payment from the advance settles the supplier's open bills
  oldest first (by due date); it used to settle the newest bill first.

## 19.0.3.7.0 (2026-10-27)

- Settlement mode on the expense report: **Cash** (as before), **Bank transfer
  (personal card)** or **Company card**.
  - Bank transfer: the advance and the difference go through the bank journal,
    on the outstanding payments / receipts account of its payment method
    (5125), so they are matched with the bank statement lines instead of being
    posted twice on 5121 (Dr 542 = Cr 5125, refund Dr 5125 = Cr 542).
  - Company card: no advance and no 542 for the receipts, which are paid by the
    company: the receipt Dr 6xx/4426 = Cr 401 is settled Dr 401 = Cr 5125 of the
    card journal (supplier partner), matched with the card statement. Only the
    per diem is owed to the employee (Dr 625 = Cr 542, paid from the payment
    journal). The card journal can be set on the employee.
- The per diem entry falls back to today when the expense date is empty (the
  entry could not be created without a date).
- The migration (`migrations/19.0.3.7.0`) sets the Bank transfer mode on the
  existing reports whose payment journal is a bank or card journal. A report
  already in the Advance state keeps its posted advance (Dr 542 = Cr 5121,
  posted directly on the bank account as before); its difference is posted at
  validation on the outstanding account (5125) of the bank journal, which must
  then be set on its payment methods.

## 19.0.3.6.0 (2026-10-27)

- Expense reports in a foreign currency. The report currency follows the
  currency of the cash journal (it can be changed in draft) and the lines
  take it. Every journal entry (advance, receipts, settlement from 542, per
  diem, difference) carries the currency amount and its company currency
  value at the exchange rate of its own date (OMFP 1802/2014 pt. 319); the
  company currency balance left on 542 is closed as exchange difference on
  665/765. The journal items of the report show the currency amount. The
  migration (`migrations/19.0.3.6.0`) keeps existing reports in the company
  currency.

## 19.0.3.5.2 (2026-10-09)

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

## 19.0.3.5.1 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.3.5.0 (2026-10-08)

- The number of per diem days now accepts one decimal (for example 2.5). For
  trips abroad the per diem is also paid for a part of a day (half up to 12
  hours), which a whole number could not hold. Existing values are kept; the
  column is converted on update.

## 19.0.3.4.2 (2026-10-07)

- Apps Store page in English (it was in Romanian), written from the 19.0 code, with
  Configuration and Usage sections, and the Romanian translation in its own tab
  (`readme/*.ro.md`). The test scenario and the comparison table are left out of the page.
  Summary in English; support address.

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
