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
