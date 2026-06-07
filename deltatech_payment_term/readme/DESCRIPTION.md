This module helps finance and sales teams quickly generate structured installment
payment terms in Odoo, eliminating the need to manually create each payment line.
Instead of building a payment schedule line by line, users fill in a simple wizard
and the system generates the complete term with the correct advance, number of
installments, and due dates automatically.

**Key features:**

- **Rate generation wizard** — a single form (name, type, advance amount/percentage,
  number of installments, day of the month) generates a full `account.payment.term`
  schedule in one click.
- **Percentage and fixed-amount modes** — supports both percent-based and fixed-value
  installment plans; the last line always uses the "balance" type to absorb rounding.
- **Installment indicator on invoices** — the `In Rates` computed field on
  `account.move` flags invoices whose payment term contains more than one line,
  allowing easy filtering and reporting.
- **Installment indicator on sale orders** — same flag (`Sale in Rates`) on
  `sale.order` so the sales team can identify orders with split payment terms at a
  glance.
- **Quick access from multiple documents** — a **Rates** smart button on invoices and
  on partner forms opens the related journal entries for that payment schedule.
- **Wizard bound to Sale Order and Invoice** — the action is available directly from
  the action menu of sale orders and invoices, so terms can be regenerated without
  leaving the document.
