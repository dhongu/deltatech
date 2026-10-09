# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## SALECUR-001 — P1: Invoice date repricing ignores the invoice line unit of measure

- **Status:** Fixed in 19.0.0.0.3. `_onchange_invoice_date()` converts the price of the first linked sale line from the sale line UoM into the invoice line UoM (`product_uom_id._compute_price`) before the currency conversion. With several linked sale lines the first one is still the price source.
- **Location:** models/account_move.py, _onchange_invoice_date().
- **Trigger:** Create an invoice linked to a sale line priced at 10 per Unit. Change the draft invoice line to Dozen with the corresponding unit price 120, then change the invoice date.
- **Actual behavior:** The onchange takes the first linked sale-line price and converts currency only. It writes 10 onto the invoice line still expressed in Dozens. It never converts the source unit price into the invoice line UoM.
- **Impact:** A valid unit change on a linked invoice can be overwritten with the wrong per-unit price, changing the amount to bill by the unit conversion ratio.
- **Evidence:** Executed the actual onchange with a same-currency sale price 10 per Unit and a Dozen invoice price 120: resulting price was 10. Native invoice UoM is editable, and native _compute_price_unit depends on product_uom_id; initial sale invoice creation normally retains the sale UoM, so this defect requires an edited line or an extension changing its unit. No database onchange/persistence test.
- **Suggested fix:** Normalize the sale price into the invoice UoM before currency conversion; define how edited or multiple-source invoice prices should be preserved or recomputed.
- **Validation needed:** Unit/Dozen and other related units, changed invoice dates/currency, manual price adjustments, multiple linked sale lines and flush/reload.

## Review limitations

Full eligible source and native sale/stock/invoice contracts inspected. Actual-method reproductions: audit_coverage/reproductions/fast_sale_currency.py. No database delivery, invoice posting or browser execution. Missing active_ids in the returned invoice action was excluded: native object-button action handling merges the active record context. Downpayment currency hook matches native recomputation structure; no further concrete defect asserted there. No fixes applied.
