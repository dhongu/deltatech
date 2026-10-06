# Bug review — Invoice Pickings Automatically

Review date: 2026-10-02. Target version: Odoo 19.

## AUTOINVOICE-001 — P1: Caught invoicing errors leave partial work in the cron transaction

- **Status:** Open.
- **Location:** models/stock_picking.py, _cron_generate_invoices().
- **Trigger:** Invoice creation succeeds but automatic posting raises a business validation error, or an invoicing operation raises a database error.
- **Actual behavior:** The broad exception handler marks the picking failed without a per-picking savepoint. For ordinary validation exceptions, preceding invoice creation remains in the transaction and can be committed alongside failed status. For SQL errors, the transaction can remain aborted, so even writing failed status raises and interrupts the job.
- **Evidence:** Executed actual AST-extracted cron with mocked invoice creation followed by posting ValueError: the created draft remained and picking became failed. The source has no savepoint or rollback around either invoice creation or posting. Mock execution proves control flow, not PostgreSQL persistence; database behavior still requires integration validation.
- **Impact:** Failed automatic invoicing can leave an unexpected draft and affect the sale's invoiced quantities, while database exceptions can prevent other queued pickings from progressing. Failed records are excluded from the cron's to_invoice domain.
- **Suggested fix:** Isolate each sale/picking invoice operation in a database savepoint, let failures roll back that unit, then record failure outside the savepoint. Define explicit retry/recovery for failed work.
- **Validation needed:** Posting validation after draft creation, SQL constraint failure, subsequent valid picking in the same run, retry without duplicate invoices and grouped pickings for one order.

## Review limitations

All eligible Python/XML source was read. Actual cron method exercised with mock records only; no invoice creation, posting, PostgreSQL transaction or live cron tests executed.
