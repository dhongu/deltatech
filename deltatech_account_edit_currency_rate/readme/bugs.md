# Bug review — Edit Currency Rate

Review date: 2026-10-02. Target version: Odoo 19.

## CUSTOMRATE-001 — P1: Custom rate changes rely on onchange instead of server recomputation

- **Status:** Fixed in 19.0.1.0.2. On invoices `currency_rate_custom` is a dependency of the native `_compute_invoice_currency_rate` (`invoice_currency_rate = 1 / custom`), so create/write recompute the line `currency_rate`, the balances and the taxes through the standard invoice synchronization; the line rate compute also depends on the custom field; changing it on a posted entry raises an error. Journal entries (non-invoice) keep the interactive onchange recomputation.
- **Location:** models/account_move.py, currency_rate_custom, onchange_currency_rate_custome(), _compute_currency_rate().
- **Trigger:** Import/RPC/ORM updates currency_rate_custom on an existing invoice, or changes it after line currency rates have already been read in the same environment.
- **Actual behavior:** Recalculation is explicitly performed only by the invoice onchange. The line compute reads move_id.currency_rate_custom but neither its own nor native dependencies include this custom field. A plain write does not call onchange or invalidate cached line rates through this dependency, and does not invoke the custom balance inverse merely because this invoice field changed.
- **Evidence:** Complete addon source inspected. Native line currency_rate is a nonstored computed field; native dependencies include invoice_currency_rate, currency/company/date, while the addon adds only currency/company/date. ORM Field.get_depends combines MRO dependencies, none naming currency_rate_custom. The only explicit custom-field recomputation is the onchange method. No database writes executed.
- **Impact:** The saved custom rate can disagree with cached line conversion and existing company-currency balances, producing different behavior for interactive edits and imported/programmatic updates.
- **Suggested fix:** Connect custom rate changes to server-side recomputation of the appropriate invoice/line conversion and balance fields, with native invoice synchronization and posted-document rules respected; do not depend solely on client onchange.
- **Validation needed:** Read existing line rates then write the custom rate, import/RPC update, form edit equivalence, clearing custom rate, taxes/payment terms and posted invoice restrictions.

## Review limitations

All eligible Python/XML source was read. Native compute and dependency collection compared; no Odoo invoice, currency or database integration tests executed.
