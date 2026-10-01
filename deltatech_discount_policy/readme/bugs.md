# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## DISCOUNTPOLICY-001 — P2: Combo child lines lose the parent discount

- **Status:** Open.
- **Location:** models/sale_order_line.py, _compute_discount().
- **Trigger:** Compute the discount on a combo child whose parent line has a 20% discount, with pricelist policy without_discount.
- **Actual behavior:** The override replaces the core compute and omits the combo_item_id branch, which propagates the linked parent discount. It computes each child from generic pricelist/base prices instead.
- **Evidence:** Executed the actual override with a child whose linked parent discount is 20 and generic child base/pricelist prices are both 100: child discount became 0. Core sale.order.line._compute_discount() explicitly assigns the linked line discount for combo items.
- **Impact:** Combo pricing can lose the intended parent discount on component lines and produce incorrect quotation totals.
- **Suggested fix:** Retain the standard combo branch before applying custom policy logic, and define consistent policy behavior across parent and child lines.
- **Validation needed:** Combo parent discount with multiple components, both policies, quantity changes, and total comparison with core behavior.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
