# Confirmed bugs

## PICKPOLICY-001 — P2: restriction compares different units, not reservation and completion

`models/stock_picking.py:40–56` compares `quantity_product_uom` with `quantity`. Native Odoo 19 computes the former from the latter in the product base unit (`stock_move_line.py:168–170`). One dozen therefore compares 12 against 1 and valid validation fails; with identical units both values remain equal even after quantity changes. Preserve an appropriate reservation/order reference and compare quantities after unit conversion.

## PICKPOLICY-002 — P2: additional products pass the new-product restriction

`models/stock_picking.py:57–69` requires zero base quantity and nonzero line quantity. A normally sized extra product line has both positive, so the forbidden additional product passes. The computed field is not a record of the original reservation. Detect additional moves/products against the intended source rather than this zero comparison.

Evidence: original method executed with isolated ORM doubles in `audit_coverage/reproductions/picking_policy_contracts.py`; no database workflow executed. Reviewed 2026-10-03.
