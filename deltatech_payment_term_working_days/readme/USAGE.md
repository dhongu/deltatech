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

## Examples

With a Monday-to-Friday schedule and the 2026 Romanian public holidays:

| Invoice date | Term | Due date |
|---|---|---|
| Friday 06.03.2026 | 3 working days | Wednesday 11.03.2026 |
| Thursday 09.04.2026 | 2 working days | Wednesday 15.04.2026 (Good Friday, Easter, Easter Monday skipped) |
| Thursday 30.04.2026 | 1 working day | Monday 04.05.2026 (1 May skipped) |
| Friday 06.03.2026 | 15 calendar days, moved | Monday 23.03.2026 instead of Saturday 21.03.2026 |

## Legal ceiling

When a line counted in working days may exceed 60 calendar days after the
invoice date, a warning is shown on the payment term. The overdue days, and the
late payment interest, are still counted in calendar days from the day after
the (moved) due date.
