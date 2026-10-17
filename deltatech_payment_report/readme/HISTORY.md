## 19.0.1.0.6 (2026-10-17)

- **Fix (PAYREPORT-002): removed the unusable *Print Preview* helper.** The
  method behind it called `report_action` on the window action of the report
  lines, which has no such method, and the module defines no PDF report, so a
  call ended in an error. The method and the `general_buttons` context that
  advertised it are removed; *Show* works as before.

## 19.0.1.0.5 (2026-10-17)

- **Fix: the *Card* payment method is again limited to bank journals.** Its
  restriction used the old `domain` key, which Odoo 19 ignores, so *Card* was
  offered on cash and credit card journals too. It now uses the `type` key.

## 19.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

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
