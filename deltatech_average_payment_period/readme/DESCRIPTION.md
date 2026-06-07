Tracks how long customers and suppliers actually take to pay, giving finance teams a concrete measure of cash-collection and payment efficiency.

For each reconciled journal entry the module records the exact payment date and computes the number of days elapsed since the invoice date. An aggregated pivot/graph report — **Average Payment Period** — is added directly to the Accounting Reports menu so managers can slice the data by partner, journal, or period at a glance.

**Key features:**

- **Payment Date** — automatically derived from the reconciliation partner line and stored on each `account.move.line`.
- **Payment Days** — difference (in days) between the invoice date and the payment date, weighted by the line amount for accurate averages across grouped data.
- **Plain Payment Days** — simplified variant limited to customer invoices (`out_invoice`) and vendor bills (`in_invoice`), excluding credit notes, for cleaner KPI reporting.
- **Average Payment Period report** — a dedicated pivot and graph view (menu: Accounting > Reporting > Average Payment Period) grouped by partner by default; filterable by date, partner, journal, and account.
- **Weighted average calculation** — when grouping rows, the average is computed as `sum(amount × days) / sum(amount)` rather than a plain arithmetic mean, preventing distortion from small-amount outliers.
