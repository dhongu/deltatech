# Confirmed bugs — 2026-10-03

## MRPCOST-001 — P1: production reports still read removed valuation layers

**Status:** Fixed in 19.0.2.0.8. Both tables use `stock.move.value` (positive
for consumed and finished moves in Odoo 19). Covered by
`test_report_with_move_values`, which renders `mrp.report_mrporder` for a done
order.

`views/mrp_production_templates.xml:77,116` maps stock_valuation_layer_ids.value on finished/raw stock moves. Native Odoo19 valuation is on stock.move.value and has no stock_valuation_layer_ids field. Rendering either nonempty table therefore fails at the mapped field lookup. Adapt both calculations to native move.value with correct direction sign.

Evidence: exact QWeb expressions inspected against current native stock_account move fields; removed relation absent. No QWeb render/database report executed.

## MRPCOST-002 — P2: cost form exposes the wrong duration field

`views/mrp_view.xml:22–24` binds duration, which is the native computed real duration in minutes (`mrp_production.py:158,485–488`). Custom cost formulas use duration_cost in hours instead. The Costs tab thus displays an unrelated computed duration with a float_time hours widget, and provides no editable field for the labor/utilities duration actually used by the calculation. Bind duration_cost and its label to the cost field with consistent units.

Evidence: full view/model read; native duration provider and custom formulas/create scaling compared. No form/browser validation executed.

## Limits

Entire module source reviewed against mrp_account _cal_price and extra_cost behavior. Quantity/UoM scaling, zero-quantity compute division and resetting extra_cost after costs are cleared remain database workflow validation concerns; not added as separately reproduced defects. No accounting/valuation/production tests executed.
