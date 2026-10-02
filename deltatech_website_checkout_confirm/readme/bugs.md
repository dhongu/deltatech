# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## CHECKOUT-001 — P1: Confirmation route bypasses the required payment threshold

- **Status:** Fixed in 19.0.1.0.4. `_checkout_confirm_can_confirm()` now refuses orders that
  still have to be signed, counts only transactions linked to this order alone (`done`/`authorized`,
  or `pending` on an offline provider) and confirms only when their sum reaches
  `_get_prepayment_required_amount()`. Covered by tests for insufficient partial payment,
  configured partial prepayment, multiple partial transactions, required signature, insufficient
  offline amount and grouped transactions. Priority P1 confirmed.
- **Location:** controllers/website_sale.py, _checkout_confirm_can_confirm() and shop_payment_confirmation().
- **Trigger:** For a draft order requiring full payment of 100, link a completed transaction for 1 and visit /shop/confirmation with that order in sale_last_order_id.
- **Actual behavior:** The guard accepts any done or authorized transaction without checking the order confirmation amount, and the route calls action_confirm() with sudo. The standard sale payment post-processing checks _is_confirmation_amount_reached() before confirming.
- **Evidence:** Executed the actual guard with an order total of 100 and a done transaction of 1: it returned True. Verified the standard threshold check in sale/models/payment_transaction.py and sale_order.py. This isolated check does not simulate an entire browser payment flow.
- **Impact:** A quotation can become a confirmed sale while the required payment is still outstanding, allowing downstream fulfillment prematurely.
- **Suggested fix:** Respect the order required-payment threshold and required signature before confirmation. Handle offline payment intent explicitly without allowing unrelated or inadequate online transactions to bypass the policy.
- **Validation needed:** Full payment, insufficient partial payment, configured partial prepayment, multiple partial transactions, required signature, and offline-provider confirmation.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. CHECKOUT-001 was fixed on 2026-10-01 with database-backed HttpCase tests (11 tests).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **CHECKOUT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

Executed the extracted current confirmation method with mocked records: underpayment rejected; full payment accepted; missing required signature rejected; pending online payment rejected (4 passing checks).
