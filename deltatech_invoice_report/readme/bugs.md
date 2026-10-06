# Bug review — Invoice Report

Review date: 2026-10-02. Target version: Odoo 19.

## INVOICEHISTORY-001 — P2: Invoice history adds refunds instead of subtracting them

- **Status:** Open.
- **Location:** models/product.py, _compute_invoice_history_sql(), both insertion branches.
- **Trigger:** A product has a posted invoice and a credit note in the same year; refresh its history or run the scheduled refresh.
- **Actual behavior:** The qty_in and qty_out CASE expressions group invoices and refunds together and add aml.quantity unchanged for both. Normal credit-note quantities are positive, so refunded quantities increase the totals rather than reducing them. The live refresh and cron use this SQL path, unlike the alternative ORM implementation which uses signed native report quantities.
- **Evidence:** Extracted the exact outgoing SUM(CASE ...) expression from the actual source and executed it in isolated SQLite with an invoice quantity 10 and refund quantity 2: result 12, net expected 8. Native account.invoice.report signs out_refund negatively; its vendor quantity sign is inverted by the module ORM history path to get net inbound quantities. Both SQL branches contain the same incorrect expression.
- **Impact:** Product invoice history overstates sales and purchases after refunds and disagrees with the native invoice analysis.
- **Suggested fix:** Apply the correct invoice/refund sign and use consistent product-unit conversion before aggregating; retain posted-document filtering.
- **Validation needed:** Customer and vendor invoices/refunds, net-zero refunds, multiple years and alternate units, cron and per-product refresh equivalence.

## Review limitations

All eligible source, including inactive/commented Python files, XML and access CSV was read. Only the actual aggregation expression was executed in isolated SQLite; no Odoo/PostgreSQL integration or cron tests executed.
