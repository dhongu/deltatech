# Confirmed bugs — integrated review 2026-10-03

## STOCKREPORT-001 — P2: quantities, weights and unit prices use planned demand

`report/stock_picking_report.py:50–54` aggregates `sm.product_qty`, computed from `product_uom_qty` (demand) by core `stock_move.py:381–384`. The native completion path with `cancel_backorder=True` skips splitting and does not replace demand. A picked transfer with demand 10 and processed quantity 4 therefore reports quantity 10 and weight for 10, while its valuation is for 4; value 40 yields unit cost 4 instead of 10. Aggregate actual completed quantities converted into the product base unit, consistent with native valuation's `_get_valued_qty()`.

Evidence: original SQL executed against isolated SQLite rows representing demand 10, done 4; local native completion and valuation source traced. Reproduction: `audit_coverage/reproductions/stock_report_contracts.py`. Odoo partial-delivery database workflow unexecuted.

## STOCKREPORT-002 — P2: outgoing value sign differs from outgoing quantity

`report/stock_picking_report.py:51,54` makes outgoing quantity negative but sums `sm.value` unchanged. Odoo 19 outgoing stock move values are positive costs (`stock_account/models/stock_move.py:337–351`). An incoming and outgoing movement of equal quantity/value cancel the quantity measure but add the amount measure. Apply the corresponding direction sign to the report amount, reviewing internal/dropship classifications too.

Evidence: original SQL on a positive outgoing native-value fixture yields negative quantity and positive amount. SQLite reproduction passed; valuation/database lifecycle unexecuted.

## STOCKREPORT-003 — P1: report bypasses native company separation

The SQL view selects all companies, while the manifest loads only a stock-manager read ACL and report views, with no company record rule for `stock.picking.report`. Source stock-move rules do not automatically apply to a separate SQL-view model. The action has no company domain either. A stock manager restricted to one company can query stock quantities, valuations and partners from other companies through the report. Add a company rule on the report model.

Evidence: all eligible module source and ACL reviewed; repository searches found no report-model company rule. Original SELECT returns both company fixture rows. This demonstrates SQL scope; an ORM access scenario on a multi-company database remains unexecuted.

## STOCKREPORT-004 — P2: zero quantity groups divide by zero

`report/stock_picking_report.py:53` divides by `COALESCE(sum(sm.product_qty),1)`, which replaces NULL but not zero. A completed picking with a zero-demand product group causes PostgreSQL division by zero when price is queried. Native move creation on an already-done picking sets state done (`stock_move.py:831–834`), so a zero-quantity added line can reach this report. Use NULLIF on the denominator and an explicit fallback for zero quantities.

Evidence: source inspection of the exact SQL expression and native done-picking create path. PostgreSQL/database reproduction not executed; SQLite returns NULL for division by zero and cannot verify PostgreSQL error behavior.

## Limits

No production changes, Odoo installation, PostgreSQL report/access test or browser test were performed. Isolated fixture results are not measured test-line coverage.
