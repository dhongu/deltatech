On any sale order:

1. Use the **Payment** button to generate a payment link (Stripe, PayPal, etc.) for the amount still due (order total minus what is already paid on posted invoices). Sharing this link with the customer lets them pay online.
2. Alternatively, use the **Confirm Payment** action (available from the order's action menu) to register a payment manually: pick the transaction, provider, payment method, amount, date and currency, then click **Confirm** (marks the transaction done) or **Add** (records it without confirming).
3. The order now shows, next to the totals:
   - **Amount Payment** — total amount actually paid (confirmed transactions plus paid/partially paid invoices).
   - **Payment Status** — one of Without, Initiated, Pending, Authorized, Partial, Done, Cancelled, color-coded (green = Done, yellow = in progress, red = Cancelled, grey = Without) in both the form and the orders list.
   - **Provider** — the payment provider used.
4. In the sale orders list, use the quick filters (Without payment, Initiated, Pending, Authorized, Done, Cancelled) to find orders by payment status.

These fields are computed and stored automatically — no configuration is required to start using them.
