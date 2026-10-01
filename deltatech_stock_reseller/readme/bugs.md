# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RESELLER-001 — P2: Cached reports are reused across different pricelists and partners

- **Status:** Open.
- **Location:** `wizard/stock_quant_report.py`, `do_execute()`, lines 90–91.
- **Trigger:** Generate a location report for partner/pricelist A, then request the same location for partner/pricelist B with Refresh Report disabled.
- **Actual behavior:** The cache lookup filters only by location and excludes the current wizard ID. It does not compare the partner, pricelist, or quantity-threshold configuration.
- **Example:** An isolated execution returned the earlier partner A report for a wizard configured with partner B and a different pricelist.
- **Impact:** The user sees reseller prices and threshold texts from another report configuration.
- **Evidence:** Executed the existing cache-selection method with a mocked previous report and captured its location-only search domain.
- **Suggested fix:** Include all report-defining options in cache matching, or refresh when those options differ.
- **Validation needed:** Same-location requests with different pricelists, partners, and threshold settings; identical settings should remain reusable.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
