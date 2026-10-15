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
