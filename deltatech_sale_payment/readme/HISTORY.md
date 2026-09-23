## 19.0.1.1.6 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.1.1.5 (2026-09-23)

- Fix: "Amount Payment" on the sale order dropped confirmed transactions that never produced an accounting payment once the invoice had any amount paid. `_compute_payment` added the amount paid on the invoice and then subtracted every post-processed transaction of that invoice, assuming its amount was already in the invoice. A transaction confirmed on a provider without a journal (e.g. orders imported from Shopify, paid by card) has no `payment_id`, so it simply vanished from the total: an order paid 382 by card at checkout plus 44 through a payment link showed 44 instead of 426, with status `partial`. Only transactions that have a `payment_id` are subtracted now.
