# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PRICE-001 — P2: Fixed included taxes are treated as percentage taxes

- **Status:** Fixed in 19.0.1.0.3. The manual `price * tax.amount / 100` loop was replaced by the Odoo tax engine: the tax-excluded base price is passed to `compute_all(..., handle_price_include=False)` on the price-included taxes only (group taxes are flattened first). Fixed, percentage, grouped and compound included taxes are now computed correctly, and taxes not included in the price are no longer added. A product with a zero base price still gets 0 on all tiers, even with a fixed included tax (unchanged behavior). Covered by `tests/test_product_price.py::TestPriceCategTaxes`.
- **Location:** `models/product.py`, `_compute_price_list()`, lines 142–148.
- **Trigger:** Calculate category prices from cost or purchase price for a product with a fixed, price-included tax.
- **Actual behavior:** The included-tax loop always calculates `price * tax.amount / 100`, ignoring the tax's amount type.
- **Example reproduced:** A base cost of 200 and an included fixed tax of 10 produce 220 before the category markup, instead of 210.
- **Expected behavior:** Fixed taxes add their fixed amount; other tax types follow Odoo's tax calculation rules.
- **Impact:** Bronze, Copper, Silver, and Gold prices are incorrect for affected tax configurations.
- **Evidence:** Isolated execution of the existing compute method reproduced the 220 result. The loop contains no amount-type branch and bypasses the Odoo tax engine.
- **Suggested fix:** Use the Odoo tax engine with a clearly defined excluded/included base rather than manually treating all taxes as percentages.
- **Validation needed:** Percentage, fixed, grouped, and compound included taxes, for each supported base-price source.

## PRICE-002 — P3: Stored category prices are not invalidated by tax-rate changes

- **Status:** Fixed in 19.0.1.0.3. Priority lowered from P2 to P3 at verification (tax rates rarely change on existing taxes). The compute now also depends on the tax properties it uses: `amount`, `amount_type`, `include_base_amount`, `price_include_override`, the company's `account_price_include` and `children_tax_ids`. Tax `sequence` is deliberately left out: it only matters for several included taxes that affect each other, and reordering taxes in the list would otherwise recompute every product using them (about 7 s per 30,000 products, measured). Covered by `test_tax_change_recomputes_prices`.
- **Location:** `models/product.py`, `_compute_price_list()` dependency declaration, lines 108–117; included-tax calculation, lines 126–147.
- **Trigger:** Change the amount, price-inclusion setting, or ordering of an existing tax linked to a product whose category prices depend on included taxes.
- **Actual behavior:** The stored price compute depends on the `taxes_id` relation, but not on the tax properties it reads. Editing an existing tax does not change that relation and therefore does not invalidate the stored category prices through this declaration.
- **Expected behavior:** Changes to tax properties affecting the computation trigger recomputation of the stored prices.
- **Impact:** Bronze, Copper, Silver, and Gold prices can retain values based on an old tax configuration until another declared dependency changes.
- **Evidence:** Compared the stored field declarations, compute dependency list, and the tax property reads. This is a dependency/invalidation finding; no database-backed recomputation test has been run.
- **Suggested fix:** Declare the relevant dotted tax dependencies, coordinated with the tax-engine correction in PRICE-001.
- **Validation needed:** Change an existing tax rate and inclusion setting without modifying the product relation; verify that stored category prices update.

## Review limitations

Verified against the local Odoo 19 source and, where stated, by isolated execution with mocked ORM objects. Both findings were fixed on 2026-10-01 and are covered by database-backed tests.

## Historical local-checkout reverification — 2026-10-01

Historical snapshot: compared the then-current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PRICE-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **PRICE-002 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.

The historical checkout result above is tied to its stated commit. It does not override the current status in this report or establish that a locally observed fix exists on the published branch. Remote documentation and fixes were preserved during publication on 2026-10-02.
