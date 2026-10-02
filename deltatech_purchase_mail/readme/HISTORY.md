## 20.0.1.1.2 (2026-10-02)

- Fix the batch email: the orders became "sent" when the composer was opened, even if the email was never sent. Now nothing changes when the composer opens; when the email is really sent, each order gets a note with the email and its own attachments (the summary and its PDF) and the RFQs are marked as sent. Previously only an internal "RFQ prepared" note was left on the order. The test no longer needs `stock` to run.

## 20.0.1.1.1 (2026-10-02)

- Migration to Odoo 20.0: access rights in `security/ir.access.csv`, attachments
  stored as raw bytes, `t-out` in the email template, XLSX description taken from
  the line label (product + description).

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
