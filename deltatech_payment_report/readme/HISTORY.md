## 19.0.1.0.3 (2026-10-02)

- **Fix (PAYREPORT-001): the payment report is no longer empty.** It searched
  customer receipts in the states `posted`/`reconciled`, which no longer exist
  on `account.payment` in Odoo 19, so no receipt was ever reported. It now
  includes receipts *In Process* and *Paid*; draft, canceled and rejected
  receipts are still excluded.

# 19.0.1.0.2

- New Apps Store banner, with the module icon, instead of the old one.

# 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

# History

## 19.0.1.0.0 (2026-09-24)

- Port from 18.0. No code changes: the wizard fields, `account.payment.method`
  override and views already followed the Odoo 19 conventions (`<list>` view,
  no `attrs`/`states`).
