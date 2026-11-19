## 19.0.1.2.0 (2026-11-19)

- Backported from 20.0 (version 20.0.1.2.0). Odoo 19 has no price matching flag on the bill
  lines, so the matching flag adaptation of 20.0 is not part of this version.

- *Vendor Rate* is no longer 0 when not typed: it shows the Odoo (BNR) rate of the bill date.
- Changing the bill date brings the Odoo rate of the new date back into *Vendor Rate*; when it
  replaces a rate typed by hand, a warning names both rates. Type the vendor rate after the bill
  date.

## 19.0.1.1.0 (2026-11-19)

- New *Vendor Rate* on the vendor bill: the rate stated on the supplier invoice (bill currency
  for 1 unit of the order currency). When set, the order prices are converted at this rate
  instead of the Odoo rate of the bill date.

## 19.0.1.0.0 (2026-11-19)

- First version: invoicing journal on the purchase order, vendor bill in the journal currency,
  prices converted at the bill date rate.
