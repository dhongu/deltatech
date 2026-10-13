# Bug review — MRP BoM Formula

Review date: 2026-10-02. Target version: Odoo 19.

## BOMFORMULA-001 — P2: Formulas only on nested phantom bills are ignored

- **Status:** Open.
- **Location:** models/mrp_bom.py, MrpBom.explode(), initial fast path.
- **Trigger:** A root bill has no formula on its immediate lines, but a nested phantom bill contains formula-driven components.
- **Actual behavior:** The override delegates to the native explosion whenever its direct lines have no qty_formula. Native explosion flattens all nested phantom bills in its own queue, multiplying current_line.product_qty without invoking child explode() or _get_formula_quantity(). Consequently nested formulas are ignored unless an unrelated root line also has a formula.
- **Evidence:** Executed actual AST-extracted override with a formula-free direct-line collection and a superclass spy: native path selected. Inspected the complete native explode(): nested lines are enqueued directly and line_quantity always uses product_qty. Example: root uses one kit, child component has stored quantity 1 and formula qty * 2; this path consumes 1 instead of 2.
- **Impact:** Manufacturing component requirements and consumption differ from formulas configured on nested bills; adding a root formula changes otherwise identical child calculation behavior.
- **Suggested fix:** Ensure formula evaluation is used across the entire traversed phantom hierarchy, including when only descendants carry formulas; avoid a direct-lines-only fast path.
- **Validation needed:** Root without formulas plus child formula, multiple nesting levels, root formula present/absent equivalence, phantom skipping and attribute inheritance.

## Review limitations

All eligible Python/XML source was read and native explosion compared. Isolated fallback mock only; no manufacturing/database integration tests executed.
