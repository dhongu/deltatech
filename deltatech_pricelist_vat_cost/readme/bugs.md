# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## VATCOST-001 — P2: Purchase VAT is skipped when sales taxes are empty

- **Status:** Fixed in 19.0.1.0.2. The guard in both `_compute_standard_price_with_vat()` implementations now checks `supplier_taxes_id`, and `@api.depends` lists `supplier_taxes_id`, `supplier_taxes_id.amount`, `supplier_taxes_id.amount_type` and `currency_id` instead of `taxes_id`. Covered by `tests/test_cost_with_vat.py` (purchase taxes only, sales taxes only, both, neither; changing the purchase taxes and the tax amount). Priority P2 confirmed.
- **Location:** `models/product.py`, both `_compute_standard_price_with_vat()` implementations, lines 12–20 and 31–39.
- **Trigger:** A product has a nonzero cost and purchase taxes, but no sales taxes.
- **Actual behavior:** The guard checks `taxes_id` (sales taxes), although the amount is calculated from `supplier_taxes_id` (purchase taxes). With empty sales taxes, the calculation is skipped.
- **Example:** Cost 100 with a purchase tax producing a total of 121 is reported as cost with VAT 100 when sales taxes are empty.
- **Expected behavior:** Cost with purchase VAT depends on purchase taxes regardless of the sales-tax configuration.
- **Impact:** VAT-inclusive cost and pricelists based on it can be understated. The declared compute dependencies also omit the purchase-tax relation used by the calculation.
- **Evidence:** Isolated execution reproduced the skipped tax-inclusive calculation; both template and variant implementations have the same guard/dependency mismatch.
- **Suggested fix:** Use the purchase-tax relation consistently for the guard and compute dependencies, including relevant tax properties.
- **Validation needed:** Products with purchase taxes only, sales taxes only, both, and neither; changing purchase taxes must invalidate the computed value.

## VATCOST-002 — P2: Purchase taxes of all companies are applied together

- **Status:** Fixed in 19.0.1.0.3. Both `_compute_standard_price_with_vat()` implementations filter the purchase taxes with `_filter_taxes_by_company(self.env.company)`, as core does for product taxes, and declare `@api.depends_context("company")`. Covered by `tests/test_cost_with_vat.py::test_multi_company_uses_current_company_taxes` and `test_pricelist_based_on_cost_with_vat`.
- **Location:** `models/product.py`, both `_compute_standard_price_with_vat()` implementations.
- **Trigger:** A product shared between companies has purchase taxes from more than one company — the default when it is created with several companies selected (`self.env.companies.account_purchase_tax_id`).
- **Actual behavior:** `compute_all()` ran on every purchase tax of the product, under `sudo()`, without filtering by company. Because `standard_price` is company-dependent but the computed field had no context dependency, reading it after switching company in the same transaction returned the value cached for the previous company.
- **Example:** Cost 100 with a 21% purchase tax in company A and an 11% one in company B was reported as 132 in company A instead of 121.
- **Impact:** VAT-inclusive cost and pricelists based on it overstated in multi-company databases.
- **Validation:** Fresh database, 8 tests, 0 failures. Against the 19.0.1.0.2 code the multi-company test fails with 132 != 121; with the company filter but without `depends_context` it fails with 121 != 222.

## VATCOST-003 — P2: cost-with-VAT pricelist base uses the wrong source currency

_Recorded as VATCOST-002 in the local audit of 2026-10-03; renumbered when syncing with origin, where VATCOST-002 already names another issue._

Both computes in `models/product.py` derive standard_price_with_vat from company-dependent standard_price, but pass product.currency_id rather than cost_currency_id to the tax engine. The custom pricelist base also falls through native `_compute_base_price`/`_price_compute` as an ordinary sales-price field: native code special-cases only standard_price for cost_currency_id, assigning product.currency_id to other bases. For a shared product, currency_id follows the main company while cost_currency_id follows the active company (`product_template.py:260–267`). A cost-with-VAT amount in B's currency can therefore be converted as if it were A's currency, distorting formula pricelist prices. Override custom-base currency handling consistently with native cost-price semantics.

Evidence: complete module compute/base selection traced into native product.pricelist.item._compute_base_price (:628–659) and product.template._price_compute (:737–771), and product currency providers. Source-supported currency mismatch; native currency-rate/pricelist database scenario unexecuted.

## Review limitations

Verified through local source and dependency analysis and the isolated reproductions stated above. The fix was validated with database-backed tests on a fresh database (6 tests, 0 failures); before the fix, 3 of them failed, and with the old dependencies the 2 invalidation tests failed.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **VATCOST-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## Integrated reverification — 2026-10-03

All eligible source read. VATCOST-001 fix remains present for purchase-tax guard/dependencies; historical database tests not rerun. Tax properties beyond listed dependencies and multiple-company supplier taxes remain integration limits. No tax/pricelist/browser tests executed.
