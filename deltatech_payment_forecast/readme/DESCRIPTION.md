Finance teams need to know when invoices will really be paid. This module estimates the payments expected on open customer and vendor invoices up to an end date, from how fast each partner usually pays.

- **Generate the forecast**: The *Generate payment forecast* menu opens a window with *End Date* and *Company*. *Compute forecast* stores a line for each posted, unpaid or partly paid invoice, bill or credit note due by that date.
- **Payment estimate**: A partner's usual delay is the average payment time of its invoices from the last 365 days. If the invoice date plus that delay falls after the end date, the line's *Payment amount* is zero; otherwise it is the open amount.
- **Report**: *Payment forecast report* lists partner, invoice, dates, amount and open amount in company currency, with form, pivot and graph views and grouping by *Days* and *Move type*.
- **Snapshots**: A manual run replaces the earlier *Custom* lines of its company. The wizard method `get_forecast_cron(days)` refreshes, for each company of the user, the snapshot labeled with that number of days; the scheduled action is not included.

The module depends on *Invoicing* and *Average Payment Period*, and the *Payment forecast* group sees the menus. The payment history comes from accounts with code 4111 (customers) or 401 (suppliers), as in the Romanian chart; a partner without history counts in full.
