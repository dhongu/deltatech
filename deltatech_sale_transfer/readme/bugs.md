# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## SALETRANSFER-001 — P1: Transfer demand mixes sale-line and product units

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `models/sale_order.py:41–90, prepare_transfer()`.
- **Trigger:** Confirm a sale line in dozens for a product whose stock unit is pieces, with a shortage at the sale warehouse and available stock elsewhere.
- **Actual behavior / impact:** The initial comparison converts the sale demand to the product unit, but the shortage then uses line.product_uom_qty - product.qty_available. Source stock is also in the product unit while move quantity is written in the sale unit. Transfers can be skipped or request far more stock than available.
- **Evidence:** Executed the extracted method with 1 dozen ordered and 6 pieces in the destination: it computes 1 - 6, treats demand as nonpositive and creates no transfer, although 6 pieces are missing.
- **Suggested fix:** Compute shortage and available stock in one unit, then convert the selected quantity to the created move unit; account consistently for repeated product lines.
- **Validation needed:** Confirm orders in pieces, dozens and mixed units; assert moved base quantities cover only the shortage and never exceed the source availability.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.
