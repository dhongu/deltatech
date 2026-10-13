Cash advances to employees, settled with an expense report, the way Romanian accounting books
them: the advance goes to account 542, the employee brings the receipts, and validating the
report books the purchase receipts, the per diem and the difference to return or to pay, until
542 is back to zero for that employee.

- **Advance on account 542**: The advance is paid from the cash journal and booked on the
  employee's 542.
- **Receipts as report lines**: Each line is a receipt, entered with VAT included; validation
  creates the purchase receipts and settles them from the advance. A line can also be a payment
  to a supplier made from the advance.
- **Per diem**: A daily amount (42.5 by default) times the number of days, booked on a travel
  expense account (625 by default).
- **Difference settled**: What is left of the advance is returned by the employee, or what was
  spent above it is paid to the employee, through the cash journal.
- **Approval roles**: Employee, Approver and Accountant: the approver validates the advance,
  only the accountant posts or reverses the report.
- **Employee view**: A smart button on the employee shows their expense reports; each report
  can be printed.

The module does not replace the standard Expenses app (`hr_expense`), which reimburses expenses
paid by employees and has no cash advance. Both can be used together; the optional module
`deltatech_expenses_hr_expense` brings standard expenses into this report without booking them
twice.
