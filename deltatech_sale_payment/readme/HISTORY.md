## 19.0.1.2.0 (2026-09-23)

Brings back what 18.0.1.2.0 (#2469, #2482) added and never reached 19.0, and replaces the 19.0.1.1.5 amount rule:

- `payment_amount`, `payment_status` and `provider_id` are stored again, with the full dependencies (transactions and invoices), so the order list can filter, group and sort on them in SQL. The Python search method is gone.
- **Amount paid = max(amount paid on the posted invoices, amount of the confirmed transactions).** A transaction confirmed on a provider without a journal (e.g. Shopify card) has no accounting payment and reaches the invoice only when the processor's settlement is reconciled, so the data cannot tell whether it is already in the invoice amount. 18.0 subtracted it (card 382 + payment link 44 showed 44); 19.0.1.1.5 added it (a settled card order showed twice its total). The maximum is right in both cases; it only underestimates an unsettled card payment completed by a manual payment on the invoice.
- New `pending` status for orders whose transactions are waiting on the provider (bank transfer, 3-D Secure...); until now they showed as `initiated`.
- The displayed provider follows the most relevant transaction: done, then authorized, pending, cancelled, then the last one.
- An order is `done` when the amount paid reaches its total within the currency rounding.
- Search filters for every status (without, initiated, pending, authorized, partially paid, paid, cancelled), a "Payment Status" group-by, and colour decorations on the form.
- The payment link proposes what is left to pay on the order (total minus the amount paid); it used to propose 0 once an invoice existed.
- Migration: the three fields are computed in SQL, set-based, before the registry loads (seconds instead of an ORM recompute of every order), for databases coming from 18.0 as well as from 19.0.1.1.x. The SQL was checked against `_compute_payment` order by order.

## 19.0.1.1.5 (2026-09-23)

- Fix: "Amount Payment" on the sale order dropped confirmed transactions that never produced an accounting payment once the invoice had any amount paid. `_compute_payment` added the amount paid on the invoice and then subtracted every post-processed transaction of that invoice, assuming its amount was already in the invoice. A transaction confirmed on a provider without a journal (e.g. orders imported from Shopify, paid by card) has no `payment_id`, so it simply vanished from the total: an order paid 382 by card at checkout plus 44 through a payment link showed 44 instead of 426, with status `partial`. Only transactions that have a `payment_id` are subtracted now.
