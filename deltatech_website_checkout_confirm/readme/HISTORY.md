## 20.0.1.0.4 (2026-10-01)

- Migration to Odoo 20.0. The confirmation logic is unchanged: `_has_to_be_signed()`,
  `_get_prepayment_required_amount()` and `payment.transaction._check_amount_and_confirm_order`
  keep their 19.0 behaviour. The native cash on delivery of Odoo 20 (`delivery`) is a `custom`
  provider, so its pending transactions are already treated as offline.

## 19.0.1.0.4

- Security: `/shop/confirmation` now respects the amount required for confirmation and the
  required signature, like the standard payment post-processing. The order is confirmed only
  when the qualifying transactions (`done`/`authorized`, or `pending` on an offline provider)
  linked only to this order cover the prepayment amount, and no signature is pending.

## 19.0.1.0.3

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.2

- Security: `/shop/confirmation` no longer confirms any order from the session. The order is
  confirmed only when it is a quotation with a `done`/`authorized` payment transaction, or a
  `pending` one on a provider without online processing (wire transfer, cash on delivery).
  Reloading the page on an already confirmed order no longer raises an error.
