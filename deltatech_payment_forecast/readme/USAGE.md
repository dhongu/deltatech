1. Go to **Accounting > Reporting > Payment forecast > Generate payment forecast** (visible to users in the **Payment forecast** security group).
2. In the wizard, set the **End Date** up to which you want to forecast payments, and confirm the **Company**.
3. Click **Compute forecast**. The module scans all posted, unpaid or partially paid customer and vendor invoices due on or before that date, estimates each partner's expected payment date from their historical average payment delay (via `deltatech_average_payment_period`), and creates forecast lines.
4. Review the results under **Accounting > Reporting > Payment forecast > Payment forecast report** (list/pivot/graph views), grouped or filtered by incoming vs. outgoing payments.
5. To automate this, schedule a cron calling `get_forecast_cron(days=N)` on the wizard model — it regenerates the forecast for "today + N days" and replaces any previous forecast for that same offset.
