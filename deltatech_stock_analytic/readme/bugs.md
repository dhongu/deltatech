# Bug review — Stock Analytic

Review date: 2026-10-02. Target version: Odoo 19.

## STOCKANALYTIC-001 — P2: Analytic value multiplies different quantity and price units

- **Status:** Open.
- **Location:** models/stock.py, write().
- **Trigger:** Complete a transfer in a unit different from the product unit, with analytic accounts on both locations and the valuation-price fallback in use.
- **Actual behavior:** The override multiplies move.quantity (in move.product_uom) by _get_price_unit() or standard_price (per product unit). It does not convert the quantity before calculating the analytic monetary amount.
- **Evidence:** Actual extracted write with quantity=1 dozen and fallback price=5 per unit created amounts +5/-5 instead of +60/-60. Native stock_account _get_price_unit divides value by _get_valued_qty; that quantity is converted into the product unit. Native analytic estimation explicitly converts move quantity before multiplication.
- **Impact:** Analytic cost transfers are understated/overstated by the unit conversion ratio.
- **Suggested fix:** Calculate monetary values using product-unit quantities or the appropriate move valuation, while keeping unit_amount and product_uom_id mutually consistent.
- **Validation needed:** Unit/dozen transfers, fractional units, returns and zero/nonzero price_unit branches.

## STOCKANALYTIC-002 — P1: Repeated done-state writes duplicate analytic entries

- **Status:** Fixed in 19.0.1.0.3. Analytic lines are created only on the actual transition into done (moves already done are skipped in write()), and each move keeps its source/destination pair in location_analytic_line_ids, so repeated or batched done writes never create a second pair.
- **Location:** models/stock.py, write().
- **Trigger:** A caller writes state=done on an already completed move with both locations configured for analytics.
- **Actual behavior:** The method checks only the incoming state value, not the previous state or existing analytic entries. Every invocation creates another source/destination pair, with no move link used to identify or update prior entries.
- **Evidence:** Executed actual extracted write twice on the same move: four analytic entries created instead of two. There is no transition guard or deduplication in the method.
- **Impact:** Retry or repeated state updates inflate analytic cost transfers; the entries cannot be reconciled to a unique creation per move by this module.
- **Suggested fix:** Create entries only for a real transition into done and retain explicit move links for idempotency and later corrections.
- **Validation needed:** Repeated ORM writes, batched completion, normal completion and correction/reversal workflows.

## Review limitations

All eligible Python/XML source was read. Existing tests were inspected but not executed. Actual methods ran only with isolated mock objects; no Odoo stock or database integration tests executed.
