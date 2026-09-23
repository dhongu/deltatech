## 18.0.1.2.1 (2026-09-23)

- Fix (port of 19.0.1.1.5): "Amount Payment" on the sale order dropped confirmed transactions that never produced an accounting payment once the invoice had any amount paid. A transaction confirmed on a provider without a journal (e.g. orders imported from Shopify, paid by card) has no `payment_id`, so subtracting it from the invoice amount made it vanish: an order paid 382 by card plus 44 through a payment link showed 44 instead of 426, with status `partial`. Only transactions that have a `payment_id` are subtracted now, and invoice transactions are read with `sudo()`.
- Migration: the stored payment fields of the orders affected are recomputed.
