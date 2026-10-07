Cash advances to employees, settled with an expense report, the way Romanian accounting books
them: the advance goes to account 542, the employee brings the receipts, and validating the
report books the purchase receipts, the per diem and the difference to return or to pay, until
542 is back to zero for that person.

- **Advance on account 542**: The advance is paid from the cash journal and booked on the
  employee's 542.
- **Receipts as report lines**: Each line is a receipt, with its VAT computed from the tax on the
  line; validation creates the purchase receipts and settles them from the advance. A line can also be a payment
  to a supplier made from the advance.
- **Per diem**: A daily amount (42.5 by default) times the number of days, booked on a travel
  expense account (625 by default).
- **Difference settled**: What is left of the advance is returned by the employee, or what was
  spent above it is paid to the employee, through the cash journal.
- **Printable report**: Each expense report can be printed.

The module does not replace the standard Expenses app (`hr_expense`), which reimburses expenses
paid by employees and has no cash advance. Both can be used in the same database.
