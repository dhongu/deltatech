# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## MRP-001 — P1: Consumption categories multiply production totals

- **Status:** Open.
- **Location:** `report/deltatech_mrp_report.py`, `init()`, finished/consumed joins and outer SUM expressions.
- **Trigger:** A production order consumes materials belonging to more than one cost category, such as raw materials and packaging.
- **Actual behavior:** The consumed subquery returns one row per production and cost category. Joining it to the finished-production aggregate repeats the planned and finished quantities and finished value once per category, then the outer SUM adds the duplicates.
- **Example:** For 10 planned and produced units valued at 100, two consumption categories make the report show 20 planned units, 20 produced units, and finished value 200.
- **Impact:** Production quantities and values are overstated; calculated unit costs are distorted.
- **Evidence:** An isolated SQL reproduction using the same join cardinality and SUM pattern produced the duplicated totals.
- **Suggested fix:** Aggregate consumed categories into one row per production before joining, or otherwise prevent multiplication of production aggregates.
- **Validation needed:** Use one production with raw and packaging costs; add a third category and verify that production totals stay constant.

## MRP-002 — P2: Planned quantities use an inverted and incomplete unit conversion

- **Status:** Open.
- **Location:** `report/deltatech_mrp_report.py`, line 90 and the `product_uom` selection.
- **Trigger:** The manufacturing order unit differs from the product template unit.
- **Actual behavior:** The report labels the result with `pt.uom_id` but calculates `s.product_qty / u.factor`, where `u` is the manufacturing order unit. The Odoo 19 conversion requires source factor divided by target factor.
- **Example:** For 2 dozen planned and a product template measured in pieces, the expression yields 0.1667 pieces instead of 24, even when there is only one consumption category.
- **Impact:** Planned quantity and the derived planned value are wrong.
- **Evidence:** Compared the SQL expression and selected unit with local Odoo 19 unit conversion.
- **Suggested fix:** Join the product template unit and apply the correct source-to-target conversion.
- **Validation needed:** Manufacturing orders using different units, including a product whose template unit also has a non-unit factor.

## MRP-003 — P1: Cost detail SQL view has no production or company access scope

- **Status:** Fixed in 19.0.1.0.6 — the view exposes `company_id` from `mrp_production`, `security/security.xml` adds a multi-company rule on `deltatech.cost.detail`, and the read ACL moved from `base.group_user` to `mrp.group_mrp_user` and `stock.group_stock_user` (the readers of `mrp.production`). Covered by tests in `tests/test_cost_detail_access.py`.
- **Location:** models/mrp_cost.py, DeltatechCostDetail; security/ir.model.access.csv; security/security.xml.
- **Trigger:** An internal user directly searches/reads deltatech.cost.detail, including production costs in companies or manufacturing orders outside their access.
- **Actual behavior:** Every base.group_user can read the cost-detail SQL model. Its view exposes all done component move cost aggregates globally, with no company field/rule. The only module record rule protects deltatech.mrp.report, not deltatech.cost.detail; production_id Many2one does not propagate parent record rules.
- **Evidence:** Full SQL/model and security source inspected. The global SQL view groups all component productions/categories, and cost-detail ACL has read permission for base.group_user. There is no cost-detail record rule or custom read scope. No database cost query executed.
- **Impact:** Production/category cost amounts and production identifiers can be enumerated across inaccessible companies, even if the main cost analysis and production forms are protected.
- **Suggested fix:** Expose company_id from production in the view and apply appropriate company/production access scope; limit cost-detail ACLs to intended manufacturing/cost users.
- **Validation needed:** Internal non-manufacturing users, multiple companies and restricted production access; direct search/read/read_group must respect the same permitted scope.

## MRP-004 — P2: Production report filters use obsolete manufacturing state values

- **Status:** Open.
- **Location:** report/deltatech_mrp_report.py, state field; report/deltatech_mrp_report.xml, state filters.
- **Trigger:** Filter Production Cost Analysis to In Production or Ready to Produce, or display/group an Odoo 19 production in progress/to_close.
- **Actual behavior:** The SQL forwards mrp.production.state but the report selection/filter still uses in_production, ready and picking_except. Native Odoo 19 production uses progress and to_close, while readiness belongs to reservation_state. The In Production filter therefore excludes actual ongoing production and valid new states lack report selection labels.
- **Evidence:** Compared the full report selection/XML with local mrp.production state=[draft,confirmed,progress,to_close,done,cancel] and separate reservation_state. No SQL/report UI execution.
- **Impact:** Ongoing/ready production cannot be selected reliably, and state displays/group labels can be missing for actual Odoo 19 values.
- **Suggested fix:** Align the report selection with native production state and model readiness separately using reservation_state if those filters remain needed.
- **Validation needed:** Draft/confirmed/progress/to_close/done/cancel orders and assigned/waiting component readiness; compare report filters with manufacturing list results.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **MRP-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **MRP-002 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.

Full eligible source review — 2026-10-02: MRP-001 and MRP-002 remain open. Added cost-detail access and state compatibility findings; no database tests rerun.
