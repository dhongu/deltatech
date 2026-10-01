# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## VATCOST-001 — P2: Purchase VAT is skipped when sales taxes are empty

- **Status:** Open.
- **Location:** `models/product.py`, both `_compute_standard_price_with_vat()` implementations, lines 12–20 and 31–39.
- **Trigger:** A product has a nonzero cost and purchase taxes, but no sales taxes.
- **Actual behavior:** The guard checks `taxes_id` (sales taxes), although the amount is calculated from `supplier_taxes_id` (purchase taxes). With empty sales taxes, the calculation is skipped.
- **Example:** Cost 100 with a purchase tax producing a total of 121 is reported as cost with VAT 100 when sales taxes are empty.
- **Expected behavior:** Cost with purchase VAT depends on purchase taxes regardless of the sales-tax configuration.
- **Impact:** VAT-inclusive cost and pricelists based on it can be understated. The declared compute dependencies also omit the purchase-tax relation used by the calculation.
- **Evidence:** Isolated execution reproduced the skipped tax-inclusive calculation; both template and variant implementations have the same guard/dependency mismatch.
- **Suggested fix:** Use the purchase-tax relation consistently for the guard and compute dependencies, including relevant tax properties.
- **Validation needed:** Products with purchase taxes only, sales taxes only, both, and neither; changing purchase taxes must invalidate the computed value.

## Review limitations

Verified through local source and dependency analysis and the isolated reproductions stated above. Fresh-database installations and database-backed integration tests have not been run. No fixes have been applied.
