Tracks how long customers and suppliers actually take to pay, giving finance teams a concrete measure of cash-collection and payment efficiency.

For each customer invoice or vendor bill line fully reconciled with its payment, the module records the exact payment date and computes the number of days elapsed since the accounting date of the invoice. An aggregated pivot/graph report — **Average Payment Period** — is added directly to the Accounting Reports menu so managers can slice the data by partner, journal, or period at a glance.

**✨ Key features:**

- **Payment Date** — automatically derived from the reconciliation partner line and stored on each `account.move.line`.
- **Payment Days** — difference (in days) between the accounting date of the invoice and the accounting date of the payment.
- **Plain Payment Days** — simplified variant computed only on customer invoices (`out_invoice`) and vendor bills (`in_invoice`); reconciled credit notes count with 0 days in its average.
- **Average Payment Period report** — a dedicated pivot and graph view (menu: Invoicing / Accounting > Reporting > Average Payment Period) grouped by partner by default; searchable by partner, reference and date, and groupable by partner or date (other fields through a custom group).
- **Weighted average calculation** — when grouping rows, in the pivot and in the graph, Payment Days is averaged as the absolute value of `sum(amount × days) / sum(amount)` rather than a plain arithmetic mean, preventing distortion from small-amount outliers.
