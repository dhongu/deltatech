## 20.0.2.2.0 (2026-10-15)

- The payment provider of a transaction is checked against the order when the
  transaction is created (value limit, partner labels, providers allowed by the
  delivery method), also for the express checkout; the express checkout no longer
  offers the delivery methods that allow only providers without express checkout.
- The partner labels that restrict the payment providers are read on the commercial
  partner, like for the delivery methods.
- `/shop/payment` preselects the payment method of the partner's preferred payment
  provider (`Payment Provider` on the partner, read on the commercial partner).
- The logo of the delivery method is shown in the shop checkout.
- Removed the unused `data-acquirer-allowed-ids` attribute and the commented-out
  templates.

## 20.0.2.1.6

- Migration to 20.0: the payment providers are filtered in `_find_available_providers`
  (it replaces `_get_compatible_providers`) and the excluded providers appear in the
  availability report with the reason.
- The weight limits on the delivery method form are visible for all delivery types.
- Removed the dead code: the commented-out `payment_form.esm.js` asset and the
  `_check_carrier_quotation` override of a method that no longer exists.

## 19.0.2.1.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.2.1.5 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.
