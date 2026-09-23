## 19.0.1.2.0 (2026-09-23)

Brings back what 18.0.1.2.0 (#2469, #2482) added and never reached 19.0, on top of the 19.0 fixes:

- `payment_amount`, `payment_status` and `provider_id` are stored again, with the full dependencies (transactions and invoice payments), so the order list can filter, group and sort on them in SQL. The Python search method is gone.
- New `pending` status for orders whose transactions are waiting on the provider (bank transfer, 3-D Secure...); until now they showed as `initiated`.
- The displayed provider follows the most relevant transaction: done, then authorized, pending, cancelled, then the last one.
- An order is `done` when the amount paid reaches its total within the currency rounding.
- Search filters for every status (without, initiated, pending, authorized, partially paid, paid, cancelled), a "Payment Status" group-by, and colour decorations on the form.
- The payment link proposes what is left to pay on the order (total minus the amount already paid through transactions or on invoices); it used to propose 0 once an invoice existed.
- Migration: the stored columns are created before the registry loads and every sale order is recomputed in batches, which also repairs the amounts computed on 18.0 before the 19.0.1.1.5 fix.

## 19.0.1.1.5 (2026-09-23)

- Fix: "Amount Payment" on the sale order dropped confirmed transactions that never produced an accounting payment once the invoice had any amount paid. `_compute_payment` added the amount paid on the invoice and then subtracted every post-processed transaction of that invoice, assuming its amount was already in the invoice. A transaction confirmed on a provider without a journal (e.g. orders imported from Shopify, paid by card) has no `payment_id`, so it simply vanished from the total: an order paid 382 by card at checkout plus 44 through a payment link showed 44 instead of 426, with status `partial`. Only transactions that have a `payment_id` are subtracted now.
