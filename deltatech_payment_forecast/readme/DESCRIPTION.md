Finance teams need to know when invoices will really be paid. This module estimates the payments expected on open customer and vendor invoices, from how fast each partner usually pays.

- **Generate the forecast**: The *Generate payment forecast* menu asks for an *End Date*. *Compute forecast* stores a line for each posted, unpaid or partly paid invoice, bill or credit note due by then.
- **Payment estimate**: A partner's usual delay is the average payment time of its invoices from the last 365 days. If the invoice date plus that delay is after the end date, the *Payment amount* is zero; otherwise it is the open amount.
- **Report**: *Payment forecast report* lists partner, invoice, dates, amount and open amount, with form, pivot and graph views and grouping by *Days* and *Move type*.
- **Snapshots**: A manual run replaces all earlier *Custom* lines. The wizard method `get_forecast_cron(days)` refreshes the snapshot labeled with that many days; the scheduled action is not included.

The module depends on *Invoicing* and *Deltatech Average Payment Period*, and the *Payment forecast* group sees the menus. The history comes from accounts whose code contains 4111 (customers) or 401 (suppliers), as in the Romanian chart; a partner without history counts in full. The forecast covers every company active in the session; its lines carry no company.
