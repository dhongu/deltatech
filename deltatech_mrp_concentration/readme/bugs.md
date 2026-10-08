# Confirmed bugs — 2026-10-03

## CONCENTRATION-001 — P1: byproduct quantity writes a prohibited stock-move field

**Status:** Fixed in 19.0.1.0.3. The by-product demand is written on
`product_uom_qty`. Covered by `test_04_production_byproduct_quantity`.

`models/mrp_production.py:45` assigns `secondary_move_line.product_qty` when primary quantity exceeds finished quantity. Native stock.move.product_qty is computed from demand and its `_set_product_qty()` inverse explicitly raises a programming-error UserError (`stock_move.py:485–490`). Write product_uom_qty after the appropriate unit conversion. The negative-difference branch therefore cannot persist the intended byproduct update reliably; onchange NewId/inverse timing requires ORM validation.

Evidence: original production onchange executed with a recordset double whose product_qty setter invokes the exact native inverse, reproducing UserError. Fixture `audit_coverage/reproductions/mrp_concentration_contracts.py`. This proves the assignment/inverse contract, not exact browser error timing.

## CONCENTRATION-002 — P2: switching dilution/concentration leaves obsolete quantities

**Status:** Fixed in 19.0.1.0.3. For every ratio, secondary ingredient =
max(diff, 0) and by-product = max(-diff, 0), on the BoM and on the MO. Covered
by `test_03_bom_switch_dilution_concentration` and
`test_04_production_byproduct_quantity`. Several secondary/by-product lines
still all receive the same quantity, as before.

`models/mrp_bom.py:24–33` updates secondary ingredient only for positive difference and byproducts only otherwise. Neither clears the opposite group. `models/mrp_production.py:33–45` repeats the same branching. Changing a20-unit recipe from primary30/byproduct10 to primary10/secondary10 leaves byproduct10; changing back retains secondary10, corrupting the material balance. Set both affected groups consistently for every ratio, including zero difference, and decide how multiple ingredient/byproduct lines are distributed.

Evidence: exact BoM onchange executed across both branches; inactive branch quantities remain10. Isolated fixture passed. MO branch uses the same source pattern but complete production state/inventory behavior is unexecuted.

## Limits

All eligible source read with native quantity fields. Formula also combines finished/component numbers without UoM normalization; concrete mixed-UoM production tests remain unexecuted and this is not separately asserted here. Multiple primary ingredients can require singleton handling; no additional finding added without its ORM scenario. No Odoo database/browser/manufacturing workflow executed.
