## 20.0.2.0.4 (2026-11-06)

- Port of 19.0.2.0.4: a new payment for the generic partner proposes an allowed journal
  by default, not the first bank journal of the company even when it is restricted.
- The **Register Payment** wizard opened from an invoice leaves out the restricted
  journals for the generic partner as well, including the journal of the invoice
  preferred payment method.
- The two limitations are removed from the description. The setting stays in the Sales
  settings on 20.0.

## 20.0.2.0.3 (2026-11-03)

- Description rewritten after the code: the generic partner is declared in the
  Sales settings, section Invoicing, and is not selected automatically in
  sales or invoicing as the old text said. The banner no longer promises it.
- Limitations: on 20.0 the journal restriction does not apply in the Register
  Payment wizard and does not replace a restricted default journal.

## 20.0.2.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.2.0.1 (2026-09-23)

- Overrides that call `super()` without returning its result now pass it on
  (pylint-odoo `missing-return`). The parent methods return `None` today, so the
  behavior is unchanged.
