## Counting a payment term in working days

1. Go to **Accounting > Configuration > Payment Terms** and open or create a
   payment term.
2. On each line under **Due Terms**, choose **Count**:
   - `Calendar Days` — standard Odoo behaviour;
   - `Working Days` — the days after the invoice date (or after the end of the
     month) skip the weekends and the public holidays of the company.

   The count does not apply to the lines due "on the X of the next month",
   whose day is fixed.
3. Tick **Move to the Next Working Day** to move every due date that falls on
   a weekend or on a public holiday to the next working day.
4. Save. The new due dates apply to the invoices and bills created or reset to
   draft from now on; posted invoices keep their due dates.

![Payment term with a line in working days, a line in calendar days and the option to move to the next working day](https://apps.odoocdn.com/apps/assets/19.0/deltatech_payment_term_working_days/working_days_payment_term.png)

The **Preview** on the right shows the due dates computed with the company
calendar for the example date.

## Examples

With a Monday-to-Friday schedule and the 2026 Romanian public holidays:

| Invoice date | Term | Due date |
|---|---|---|
| Friday 06.03.2026 | 3 working days | Wednesday 11.03.2026 |
| Thursday 09.04.2026 | 2 working days | Wednesday 15.04.2026 (Good Friday, Easter, Easter Monday skipped) |
| Thursday 30.04.2026 | 1 working day | Monday 04.05.2026 (1 May skipped) |
| Friday 06.03.2026 | 15 calendar days, moved | Monday 23.03.2026 instead of Saturday 21.03.2026 |

An invoice of Thursday 09.04.2026 with the term above: the first installment
(3 working days) skips Good Friday, Easter and Easter Monday and falls due on
16.04.2026; the second one (30 calendar days, Saturday 09.05.2026) moves to
Monday 11.05.2026. The printed invoice lists both due dates.

![Printed invoice with the installments and their due dates](https://apps.odoocdn.com/apps/assets/19.0/deltatech_payment_term_working_days/working_days_invoice_due_dates.png)

## Legal ceiling

When a line counted in working days may exceed 60 calendar days after the
invoice date, a warning is shown on the payment term. The overdue days, and the
late payment interest, are still counted in calendar days from the day after
the (moved) due date.

![Warning on a payment term of 45 working days](https://apps.odoocdn.com/apps/assets/19.0/deltatech_payment_term_working_days/working_days_legal_warning.png)
