This module sends your customers automatic e-mail reminders for their invoices:
a few days before the due date, on the due date, or some days after it. For each
reminder step (a *followup*) you choose the reference date, the offset in days
and the mail template, and the e-mail can list the invoices concerned together
with the customer's totals.

**✨ Key features:**

- **Reminder steps you configure yourself**: the date used (invoice date or due
  date), the offset in days (`-2` means two days before, `3` three days after),
  and whether only that exact day or every day from then on is processed.
- **Open invoices only**: credit notes are optional, and totals are shown in the
  company currency or in the customer currency.
- **Your own mail template**: set on the Contact, with the invoices inserted where
  you place `[invoices]`, one row per invoice (number, dates, payment term,
  amounts), plus the total to pay, the customer's total debit and the amount
  already overdue.
- **Only the customers you flag**: those with *Send followup e-mails* ticked receive
  reminders.
- **Amount margin**: nothing is sent when the invoices in the e-mail add up to
  less than the margin (or to a negative amount, when credit notes exceed the
  invoices), and a note on the customer says why.
- **Amounts and dates in the customer's language**: credit notes are shown negative
  and subtracted from the total.
- **Errors stay local**: if one customer cannot be processed (for example an
  unknown placeholder), the error is logged and noted on that customer, and all
  the other customers are still processed.
- **Run from a scheduled action**: for all the followups or only for those with
  given codes, so different steps can run at different times.
