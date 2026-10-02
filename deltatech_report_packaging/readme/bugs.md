# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## PACKMAT-001 — P2: Packaging material totals ignore invoice unit conversion

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `models/account_move.py:37–61, refresh_packaging_material()`.
- **Trigger:** Invoice a product in dozens when packaging quantities are configured per piece, or mix invoice units for the same product.
- **Actual behavior / impact:** The method groups raw line.quantity by product and multiplies it by the configured material quantity. It never converts product_uom_id to product.uom_id, so equivalent physical quantities report different packaging consumption.
- **Evidence:** Executed the extracted refresh method for 1 dozen with 0.1 material units configured per product piece: it emitted 0.1 instead of 1.2. Source aggregation does not read invoice line UoM.
- **Suggested fix:** Convert each invoice line quantity to the product base unit before grouping and multiplying by material quantities.
- **Validation needed:** Compare packaging totals for 12 pieces versus 1 dozen, mixed-unit lines, purchase invoices and refunds.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.
