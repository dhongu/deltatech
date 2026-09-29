## 19.0.1.0.4 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.3 (2026-09-24)

- Port to Odoo 19: `_default_inbound_payment_methods` and
  `_get_payment_method_information` are unchanged in the `account` core
  on O19, so the code is ported verbatim (no API adaptation at all).
  Needed for the migration of the Ridacon customer (18.0→19.0): the
  "Card Payment" payment method is in active production use there.
