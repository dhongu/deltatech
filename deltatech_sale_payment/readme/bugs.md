# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEPAY-001 — P1: Partial foreign-currency payments can mark orders fully paid

- **Status:** Fixed in 19.0.1.2.2. `_compute_payment` takes the invoice side from `amount_total - amount_residual` in the invoice currency (negative for credit notes) instead of the `*_signed` company-currency amounts; invoices and transactions in a currency other than the order's are converted at the document date (`_payment_to_order_currency`). The max(invoice, transactions) deduplication policy is unchanged. The SQL of the 19.0.1.2.0 migration uses the invoice currency too, and the 19.0.1.2.2 post-migration recomputes the orders in a foreign currency. Tests: `TestSaleOrderPaymentForeignCurrency` (partial and full payment of a EUR order in a USD company at rate 5, full credit note); the partial case failed before the fix with 250 instead of 50.
- **Priority:** P1 kept: it affects only orders in a currency other than the company's, but there it shows `done` and the payment link proposes 0.
- **Location:** models/sale.py, _compute_payment(), lines 59–91.
- **Trigger:** Create a EUR 100 order in a RON company, invoice it at 5 RON/EUR, and reconcile EUR 50 without a completed payment transaction.
- **Actual behavior:** The computation mixes invoice amounts in company currency with transaction amounts and order totals in order currency. It records 250 as the amount paid and sets payment_status to done instead of recording EUR 50 as partial.
- **Evidence:** Executed the existing method extracted from its AST against minimal records: signed invoice total 500, residual 250, order total 100, no transactions; result payment_amount=250 and payment_status=done.
- **Impact:** Payment status and remaining-payment calculations can incorrectly indicate that no further payment is due.
- **Suggested fix:** Normalize all sources into the order currency using an explicit conversion date and preserve the intended invoice/transaction deduplication policy.
- **Validation needed:** Partial and full payments in both currency directions, exchange-rate changes, refunds, and transaction/invoice overlap.

## SALEPAY-002 — P2: "Confirm Payment" date is never stored

- **Status:** Open. Found while writing the consultant sheet (2026-10-01).
- **Location:** wizard/sale_confirm_payment.py, do_confirm().
- **Actual behavior:** `payment_date` is only passed as `with_context(payment_date=...)`; nothing reads it, so the date shown in the wizard is lost.

## SALEPAY-003 — P1: "Confirm Payment" deletes a done or authorized transaction

- **Status:** Open.
- **Location:** wizard/sale_confirm_payment.py, default_get() and update_transaction().
- **Actual behavior:** the `and`/`or` precedence in default_get picks up the last transaction also when it is `done` or `authorized`; update_transaction then calls `_set_canceled()` (no effect on `done`) and `unlink()`, and do_add_payment creates a new one. On an electronic provider the accounting payment of the old transaction remains and post-processing creates a second one.

## SALEPAY-004 — P2: a salesman without Invoicing rights cannot confirm

- **Status:** Open.
- **Actual behavior:** `payment.transaction` is accessible only to `account.group_account_invoice` (no unlink) and `base.group_system`; the wizard writes without sudo, so a sales-only user gets an access error on Confirm and Add.

## SALEPAY-005 — P2: confirmed wire-transfer transactions fail post-processing

- **Status:** Open.
- **Actual behavior:** Odoo 20 has no `account.payment.method` for the `custom` provider code, so after the wizard sets a wire-transfer transaction `done`, `_post_process` raises "Please define a payment method line on your payment." in `_create_payment`. The cron rolls back (order not confirmed, no invoice, no payment) and retries on the daily run for one day.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run at review time. SALEPAY-001 was fixed on 2026-10-01 with database-backed tests.
