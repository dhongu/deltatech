# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## EXPLAIN-001 — P2: Internal transfers are reported as replenishment demand and receipts

- **Status:** Open.
- **Location:** models/stock_orderpoint.py, _explain_scheduled_moves()/beyond-horizon risk; views/replenishment_explanation_templates.xml.
- **Trigger:** An open transfer moves stock between two child locations within the reordering rule location, especially after the lead horizon.
- **Actual behavior:** Incoming checks destination child_of only; outgoing/beyond checks source child_of only. A transfer entirely inside the location subtree is counted as both receipt and demand, and a future internal transfer is reported as invisible demand that can cause a stockout.
- **Evidence:** Complete move-domain source inspected against local stock product _get_domain_locations_new: native forecast excludes movements whose source and final destination remain inside the same location scope. The explanation omits these exclusions and final-destination handling. No Odoo move/search executed.
- **Impact:** The dialog presents gross internal movement as external supply/demand and can raise false stockout warnings for stock that never leaves the warehouse. Multi-step transfers can also differ from native forecast when location_final_id is relevant.
- **Suggested fix:** Reuse the product forecast location domains, including source/destination exclusions and final destination semantics, for scheduled and beyond-horizon flow totals.
- **Validation needed:** Child-to-child transfer before/after horizon, true outbound demand, incoming supply and multi-step routes; internal transfers must not change displayed supply/demand or trigger a beyond-horizon stockout warning.

## Review limitations

All eligible Python/XML source manually reviewed: horizon/lead time, quantities/rounding, risks, SVG geometry, wizard rendering, QWeb template and server action. Compared location flow semantics with local Odoo core. No Odoo forecast, SQL movement, QWeb rendering or integration test executed.
