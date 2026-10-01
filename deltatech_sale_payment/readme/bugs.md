# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEPAY-001 — P1: Partial foreign-currency payments can mark orders fully paid

- **Status:** Open.
- **Location:** models/sale.py, _compute_payment(), lines 59–91.
- **Trigger:** Create a EUR 100 order in a RON company, invoice it at 5 RON/EUR, and reconcile EUR 50 without a completed payment transaction.
- **Actual behavior:** The computation mixes invoice amounts in company currency with transaction amounts and order totals in order currency. It records 250 as the amount paid and sets payment_status to done instead of recording EUR 50 as partial.
- **Evidence:** Executed the existing method extracted from its AST against minimal records: signed invoice total 500, residual 250, order total 100, no transactions; result payment_amount=250 and payment_status=done.
- **Impact:** Payment status and remaining-payment calculations can incorrectly indicate that no further payment is due.
- **Suggested fix:** Normalize all sources into the order currency using an explicit conversion date and preserve the intended invoice/transaction deduplication policy.
- **Validation needed:** Partial and full payments in both currency directions, exchange-rate changes, refunds, and transaction/invoice overlap.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
