# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## DISCOUNTPOLICY-001 — P2: Combo child lines lose the parent discount

- **Status:** Fixed in 19.0.1.0.2. `_compute_discount()` now follows the core compute step by step and only adds the `with_discount` policy: combo item lines take the discount of their combo line, and nothing is recomputed when the discount feature is off (a manual discount is kept). Covered by `tests/test_discount_policy.py`.
- **Location:** models/sale_order_line.py, _compute_discount().
- **Trigger:** Compute the discount on a combo child whose parent line has a 20% discount, with pricelist policy without_discount.
- **Actual behavior:** The override replaces the core compute and omits the combo_item_id branch, which propagates the linked parent discount. It computes each child from generic pricelist/base prices instead.
- **Evidence:** Executed the actual override with a child whose linked parent discount is 20 and generic child base/pricelist prices are both 100: child discount became 0. Core sale.order.line._compute_discount() explicitly assigns the linked line discount for combo items.
- **Impact:** Combo pricing can lose the intended parent discount on component lines and produce incorrect quotation totals.
- **Suggested fix:** Retain the standard combo branch before applying custom policy logic, and define consistent policy behavior across parent and child lines.
- **Also found on verification (2026-10-01):** the override also dropped the core `_is_discount_feature_enabled()` and `product_uom_id` checks, so with the discount feature off it rewrote manual discounts. Fixed by the same change.
- **Validation needed:** Combo parent discount with multiple components, both policies, quantity changes, and total comparison with core behavior.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. DISCOUNTPOLICY-001 was fixed and covered by tests on 2026-10-01.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **DISCOUNTPOLICY-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
