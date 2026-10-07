A bridge between the standard Odoo Expenses app (`hr_expense`) and the Terrabit expense report
for cash advances (`deltatech_expenses`, account 542), for companies that use both and want to
avoid booking the same expense twice.

- **Import HR expenses into the report**: The **Preia cheltuieli HR** button on the expense
  report adds the employee's submitted or approved expenses as report lines.
- **Send from the expense list**: The **Adaugă în decont de cheltuieli** action sends several
  selected expenses to a chosen report in one step.
- **No double booking**: An expense linked to a report is posted only through the report; its
  own posting buttons are hidden.
- **Released on cancel**: When a report is cancelled, its imported lines are removed and the
  expenses become available again.
- **Installed automatically**: The module installs itself when both `deltatech_expenses` and
  `hr_expense` are present; no configuration is needed.
