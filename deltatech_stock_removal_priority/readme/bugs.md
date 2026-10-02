# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PRIORITY-001 — P2: Product category changes leave stored removal priorities stale

- **Status:** Fixed in 19.0.1.0.2. `_compute_removal_priority` now also depends on `product_id.categ_id` and `location_id.usage`. A new `ir.config_parameter` override recomputes the quants holding the old default when `stock.removal_priority.default` is created, changed or deleted. Tests: `test_04`, `test_05`, `test_07`. Volume check on 10,000 quants: changing the category of 2,000 products went from 27 to 150 SQL queries (about +0.8 s). Quantity updates and product writes that do not touch the category run the same number of queries as before.
- **Location:** models/stock_quant.py, removal_priority and _compute_removal_priority(), lines 12–71.
- **Trigger:** Create category-based putaway rules with different priorities for categories A and B, then move a stocked product from category A to B without changing its quant location.
- **Actual behavior:** The stored computation reads product_id.categ_id but declares only product_id and location_id as dependencies. Editing the category does not invalidate existing quant priorities. Putaway-rule hooks do not run when only the product category changes.
- **Evidence:** Source inspection of the stored compute dependency declaration and putaway-rule create/write/unlink recomputation hooks. No database reproduction was run.
- **Impact:** The priority removal strategy continues reserving stock using the previous category rules.
- **Suggested fix:** Add product_id.categ_id to stored dependencies and review invalidation for other mutable inputs, including location usage and default configuration.
- **Validation needed:** Change category A to B with existing quants and different matching rule sequences; verify priority and reservation order without an intervening stock move.

## PRIORITY-002 — P2: Archiving putaway rules leaves their stored removal priorities active

- **Status:** Fixed in 19.0.1.0.2. `active` was added to the fields that trigger recomputation in `stock.putaway.rule.write()`, so both archiving and restoring a rule are covered. Test: `test_06`.
- **Location:** models/stock_putaway_rule.py, write(); models/stock_quant.py, _compute_removal_priority().
- **Trigger:** Use an active product/category putaway rule with priority 5 for existing quants, then archive the rule by writing active=False without changing its sequence or location.
- **Actual behavior:** The write override only invalidates priorities for sequence, product_id, category_id, and location_out_id changes. active is omitted, so existing quants retain priority 5 even though a fresh computation would exclude the archived rule and use another rule or the default. Reactivation can leave the reverse stale value.
- **Evidence:** Source inspection: core stock.putaway.rule defines active, the priority compute uses the default active-rule search, and the rule write override does not recompute on active changes. No database reproduction was run.
- **Impact:** Stock reservation continues following disabled rule priorities until an unrelated recomputation occurs.
- **Suggested fix:** Invalidate affected quant priorities when active changes, covering both archiving and reactivation.
- **Validation needed:** Archive and reactivate rules with existing quants, competing active rules, and fallback to the configured default.

## Review limitations

Findings were first based on source inspection. Both were confirmed on origin/19.0 on 2026-10-01 and reproduced by database-backed tests (`tests/test_stock_removal_priority.py`, which fail before the fix). Both are fixed in 19.0.1.0.2.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PRIORITY-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
- **PRIORITY-002 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
