## 19.0.1.0.2 (2026-10-09)

- Fix CUSTOMRATE-001: the custom currency rate is applied server side. On invoices it now
  drives the native invoice currency rate, so a create/write through RPC, import or ORM
  recomputes the line rates, the company-currency balances and the taxes, exactly as the
  form does. Clearing it restores the official rate. It can no longer be changed on a posted
  entry (read-only in the form, blocked on write).
- The custom rate is no longer copied when an invoice is duplicated; a reversal (credit
  note) keeps the rate of the original document, so it is regularized with the same
  amounts in company currency.
- Help text on the field: only a rate allowed by Art. 290 of the Fiscal Code.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
