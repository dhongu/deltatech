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

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run at review time. SALEPAY-001 was fixed on 2026-10-01 with database-backed tests.
