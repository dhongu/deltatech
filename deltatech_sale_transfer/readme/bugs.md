# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## SALETRANSFER-001 — P1: Transfer demand mixes sale-line and product units

- **Status:** Fixed in 19.0.1.0.2 — `prepare_transfer()` computes the shortage as the line demand converted to the product unit minus the free destination stock, caps it to the remaining source stock, creates the move in `product.uom_id`, and tracks destination/source stock already used by repeated lines of the same product. Covered by tests in tests/test_sale_transfer_uom.py.
- **Location:** `models/sale_order.py:41–90, prepare_transfer()`.
- **Trigger:** Confirm a sale line in dozens for a product whose stock unit is pieces, with a shortage at the sale warehouse and available stock elsewhere.
- **Actual behavior / impact:** The initial comparison converts the sale demand to the product unit, but the shortage then uses line.product_uom_qty - product.qty_available. Source stock is also in the product unit while move quantity is written in the sale unit. Transfers can be skipped or request far more stock than available.
- **Evidence:** Executed the extracted method with 1 dozen ordered and 6 pieces in the destination: it computes 1 - 6, treats demand as nonpositive and creates no transfer, although 6 pieces are missing.
- **Suggested fix:** Compute shortage and available stock in one unit, then convert the selected quantity to the created move unit; account consistently for repeated product lines.
- **Validation needed:** Confirm orders in pieces, dozens and mixed units; assert moved base quantities cover only the shortage and never exceed the source availability.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.
