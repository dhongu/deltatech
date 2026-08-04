## 19.0.2.2.0 (2026-08-04)

- Validating a transfer no longer marks it as `delivered` when no carrier is
  found. That test read an unfinished transfer as a finished delivery: with a
  shipping integration at `rate` level the operator validates first and sends to
  the shipper afterwards, so `carrier_id` is empty on both the picking and the
  order for as long as the shipping wizard takes. Parcels reached `delivered`
  within the same second as the validation, which pushed the order to its
  delivered phase — and, with a carrier already on the order, mailed the
  customer — while the label was still being printed. Verified on Sanodor
  production, where three transfers went `draft -> delivered -> pre_advice` in
  about a minute, and the orders stayed on the delivered phase (`set_phase`
  never demotes). A wrong `delivered` is also excluded from the delivery status
  cron, so nothing brought those back on its own.
- The two cases — a transfer that will never have a carrier and one that does
  not have it *yet* — are indistinguishable at validation time, on the same
  operation type and with the same field values; what separates them is whether
  an AWB shows up afterwards. The carrier-less transfers are therefore marked
  `delivered` by the delivery status cron in `deltatech_delivery` (18.0.5.7.0)
  once a grace period has passed without one, instead of at validation time.
  Installations without `deltatech_delivery` keep the transfers on `draft`. Ported from 18.0.

## 19.0.2.1.4 (2026-06-11)

- Fix: releasing a postponed delivery when the payment is confirmed never
  worked — `_set_done` accessed the non-existent field
  `payment.transaction.sale_order_id` (the correct field is
  `sale_order_ids`), raising AttributeError for providers with
  *Postponed Delivery* enabled. All linked postponed orders are now
  released, and a failure to release no longer blocks the payment
  processing (logged instead).
- Added `@api.depends("picking_ids.postponed")` on
  `_compute_postponed_delivery` so the value is recomputed within the same
  transaction after postpone/release.
- Added tests for the postpone/release flow and the payment-driven release.
