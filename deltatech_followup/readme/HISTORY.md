## 19.0.0.1.4 (2026-10-29)

- Fix: the amount margin is now compared with the total of the invoices included in the followup, not with the partner's overdue debit. Followups sent before or on the due date were skipped for partners without other overdue invoices.
- Fix: credit notes included in a followup are now subtracted from the total to pay (they were added) and shown with a negative sign; the total uses the same currency as the `$currency` placeholder.
- Amounts in the e-mail are formatted in the language of the partner.
- The "Followup not sent" note is translatable and uses the currency format of the followup totals.
- Fix: `$payment_term_id` shows the name of the payment term instead of the technical recordset text.
- Fix: a followup whose invoices total a negative amount (credit notes over invoices) is no longer sent.
- Fix: a partner without language or an error on one partner (invoice without due date, unknown placeholder) no longer stops the whole run; the error is logged and noted on the partner.
- The mail template is required on the followup form (a followup without template failed for every partner).
- Followup form: options moved to the right column; list shows the comparator and the mail template; help texts and Romanian translation updated.

## 19.0.0.1.3 (2026-10-04)

- Add unit tests covering followup date matching, residual amount computation and the followup mail sending wizard (codes filter, margin skip, refunds, customer currency, override partner).

## 19.0.0.1.2 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.
