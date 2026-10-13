## 19.0.1.1.2 (2026-10-02)

- Fix the batch email: the orders became "sent" when the composer was opened, even if the email was never sent. Now nothing changes when the composer opens; when the email is really sent, each order gets a note with the email and its own attachments (the summary and its PDF) and the RFQs are marked as sent. Previously only an internal "RFQ prepared" note was left on the order. The test no longer needs `stock` to run.

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
