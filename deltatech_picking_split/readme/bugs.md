# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## PICKSPLIT-001 — P2: The split wizard copies base-unit forecast into move-unit kept quantity

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `wizard/stock_picking_manual_backorder.py:27–34, default_get()`.
- **Trigger:** Open the split wizard on a move whose product_uom differs from the product stock unit.
- **Actual behavior / impact:** product_uom_qty is in the move unit, while forecast_availability is computed in the product stock unit. The wizard copies the forecast directly into kept_qty, then subtracts kept_qty from move demand without conversion. Defaults and the resulting split quantities are wrong; the onchange may clamp a numerically larger forecast to the full demand even when only part of it is available.
- **Evidence:** Compared local stock.move._compute_forecast_information and product_qty usage. Executed the extracted default_get with demand 1 dozen and forecast 6 pieces: it emitted demand 1 and kept_qty 6.
- **Suggested fix:** Convert forecast from product.uom_id to move.product_uom before applying bounds and populating kept_qty.
- **Validation needed:** Open and execute splits in dozens with half a dozen available; expect 0.5 dozen retained and 0.5 dozen backordered.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.


## PICKSPLIT-002 — P1: RPC quantities can create negative backorders and inflate demand

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `wizard/stock_picking_manual_backorder.py:37–83, do_create_backorder(); onchange_kept_qty()`.
- **Trigger:** Set kept_qty above demand or below zero through ORM/RPC, bypassing the browser onchange, and invoke do_create_backorder.
- **Actual behavior / impact:** The only bounds check is an onchange. The server action blindly writes kept_qty as original demand and copies demand - kept_qty to the backorder. An excessive kept quantity inflates the original demand and generates a negative backorder quantity.
- **Evidence:** Executed the extracted server action with demand 1 and kept_qty 2: the original demand was set to 2 and the copied move received product_uom_qty -1.
- **Suggested fix:** Validate every line against 0 <= kept_qty <= current move demand before copying or writing, using UoM precision; revalidate transfer state and ownership at execution time.
- **Validation needed:** RPC-test negative/excess kept quantities and stale wizard demand; assert failure without changing the original or creating a backorder.
- **Limitations:** Source comparison and isolated executions of extracted current methods with mocked records; no database-backed integration tests were executed.
