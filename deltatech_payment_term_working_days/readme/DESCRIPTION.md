This module lets a payment term count its days in working days instead of
calendar days, and move a due date that falls on a weekend or on a public
holiday to the next working day. Standard Odoo counts calendar days only, so
a "3 days" term issued on a Friday falls due on Monday, and a 30-day term may
fall due on a Saturday or on Christmas.

**✨ Key features:**

- **Working days per line** — each line of a payment term counts its days in
  `Calendar Days` (the default, unchanged behaviour) or in `Working Days`. An
  installment plan can mix both.
- **Move to the next working day** — an option on the payment term moves every
  due date that falls on a non-working day to the next working day. It applies
  to calendar and working-day lines alike.
- **Company calendar** — the working days are those of the company's working
  schedule; the public holidays are the time off of the company that is not linked to a
  resource. Without a working schedule, Monday to
  Friday are working days.
- **Movable holidays** — Easter, Pentecost and any other holiday entered as
  public time off are taken into account, for every year.
- **Everywhere the due date is used** — the invoice due date, the due date of
  each installment line, the aged receivable and payable reports and the
  follow-ups all read the adjusted dates.
- **Legal ceiling warning** — the payment term form warns when a line counted
  in working days may exceed 60 calendar days, the usual legal ceiling of the
  payment terms between professionals (EU Directive 2011/7/EU).
