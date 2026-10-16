## 19.0.1.1.4 (2026-10-16)

- Fix the XLSX summary: an order reference, product code or line description starting with "=" was stored as an Excel formula in the file sent to the vendor. These columns are now always written as text.

## 19.0.1.1.3 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.1.2 (2026-10-02)

- Fix the batch email: the orders became "sent" when the composer was opened, even if the email was never sent. Now nothing changes when the composer opens; when the email is really sent, each order gets a note with the email and its own attachments (the summary and its PDF) and the RFQs are marked as sent. Previously only an internal "RFQ prepared" note was left on the order. The test no longer needs `stock` to run.

## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
