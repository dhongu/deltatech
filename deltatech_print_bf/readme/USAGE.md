This module is marked obsolete and mainly provides technical fields used by other Deltatech fiscal-printer/cash-register integrations; there is no standalone workflow to run.

- On **Accounting > Configuration > Journals**, a sales journal has a **Cod ECR** field to record which fiscal-register payment code it corresponds to (cash, voucher, card, subtotal, foreign currency, etc.).
- In **Accounting > Configuration > Settings**, a **Journal Receipt** field lets you pick the default sales journal used for fiscal receipts.
- Invoices gained a `receipt_print` flag to track whether a fiscal receipt was already printed for them.
