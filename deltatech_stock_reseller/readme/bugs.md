# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RESELLER-001 — P2: Cached reports are reused across different pricelists and partners

- **Status:** Fixed in 19.0.1.0.4. `do_execute()` now matches cached reports through `_get_cache_domain()` on location, partner, reseller pricelist and the thresholds option; when thresholds are shown, the threshold values and texts must match too. A refresh deletes only the reports with the same options, so other configurations stay available. Covered by `test_04_cache_not_reused_for_other_configuration`.
- **Location:** `wizard/stock_quant_report.py`, `do_execute()`, lines 90–91 (before the fix).
- **Trigger:** Generate a location report for partner/pricelist A, then request the same location for partner/pricelist B with Refresh Report disabled.
- **Actual behavior:** The cache lookup filters only by location and excludes the current wizard ID. It does not compare the partner, pricelist, or quantity-threshold configuration.
- **Example:** An isolated execution returned the earlier partner A report for a wizard configured with partner B and a different pricelist.
- **Impact:** The user sees reseller prices and threshold texts from another report configuration.
- **Evidence:** Executed the existing cache-selection method with a mocked previous report and captured its location-only search domain.
- **Suggested fix:** Include all report-defining options in cache matching, or refresh when those options differ.
- **Validation needed:** Same-location requests with different pricelists, partners, and threshold settings; identical settings should remain reusable.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run during the review. RESELLER-001 was fixed and verified with a database test on 2026-10-01. Cached reports are still shared between users (the model is accessible to `base.group_user`); this is intended, as the content depends only on the report options.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **RESELLER-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## RESELLER-002 — P2: optional empty pricelist loses the price currency

`wizard/stock_quant_report.py:48,75` permits an empty pricelist and calls native `_get_product_price()` on it. Native `_compute_price_rule()` supports the empty recordset and falls back to the current company currency (`product_pricelist.py:191–194`). The report then writes `reseller_currency_id` from the empty pricelist rather than the effective currency, leaving the monetary price without its currency. The form makes neither partner nor pricelist required, so generating directly from the location triggers this. Use the same currency fallback or require a pricelist.

Evidence: exact custom call/value assignment and native empty-pricelist fallback inspected. No Odoo database/browser reproduction executed. Existing RESELLER-001 cache-option fix remains present. Reviewed 2026-10-03.
