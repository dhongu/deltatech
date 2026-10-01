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

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
