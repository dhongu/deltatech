# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PRIORITY-001 — P2: Product category changes leave stored removal priorities stale

- **Status:** Open.
- **Location:** models/stock_quant.py, removal_priority and _compute_removal_priority(), lines 12–71.
- **Trigger:** Create category-based putaway rules with different priorities for categories A and B, then move a stocked product from category A to B without changing its quant location.
- **Actual behavior:** The stored computation reads product_id.categ_id but declares only product_id and location_id as dependencies. Editing the category does not invalidate existing quant priorities. Putaway-rule hooks do not run when only the product category changes.
- **Evidence:** Source inspection of the stored compute dependency declaration and putaway-rule create/write/unlink recomputation hooks. No database reproduction was run.
- **Impact:** The priority removal strategy continues reserving stock using the previous category rules.
- **Suggested fix:** Add product_id.categ_id to stored dependencies and review invalidation for other mutable inputs, including location usage and default configuration.
- **Validation needed:** Change category A to B with existing quants and different matching rule sequences; verify priority and reservation order without an intervening stock move.

## PRIORITY-002 — P2: Archiving putaway rules leaves their stored removal priorities active

- **Status:** Open.
- **Location:** models/stock_putaway_rule.py, write(); models/stock_quant.py, _compute_removal_priority().
- **Trigger:** Use an active product/category putaway rule with priority 5 for existing quants, then archive the rule by writing active=False without changing its sequence or location.
- **Actual behavior:** The write override only invalidates priorities for sequence, product_id, category_id, and location_out_id changes. active is omitted, so existing quants retain priority 5 even though a fresh computation would exclude the archived rule and use another rule or the default. Reactivation can leave the reverse stale value.
- **Evidence:** Source inspection: core stock.putaway.rule defines active, the priority compute uses the default active-rule search, and the rule write override does not recompute on active changes. No database reproduction was run.
- **Impact:** Stock reservation continues following disabled rule priorities until an unrelated recomputation occurs.
- **Suggested fix:** Invalidate affected quant priorities when active changes, covering both archiving and reactivation.
- **Validation needed:** Archive and reactivate rules with existing quants, competing active rules, and fallback to the configured default.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
