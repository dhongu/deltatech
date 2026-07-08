This module is mostly a backend fix, not a new screen. It adds a `month_of_the_year`
field on payment term lines (`account.payment.term.line`) and corrects the due-date
calculation (`account.payment.term.compute()`) so that when a line specifies an exact
month, the due date is shifted to that month/day instead of only applying a relative
day-of-month offset.

- No action is required to benefit from the corrected due-date calculation on existing
  payment terms: it is applied automatically whenever Odoo computes due dates from
  **Accounting > Configuration > Invoicing > Payment Terms**.
- The `month_of_the_year` field itself is not exposed in any standard view in this
  version (the sample view included in the module is disabled); it is meant as a
  technical hook for other Deltatech modules or developer/XML-data configuration of
  payment term lines, not for direct end-user editing.
