# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## RECEIPT-001 — P1: Automatic receipt deletes moves that already have a quantity

- **Status:** Fixed in 19.0.2.0.2. `receipt_to_stock()` no longer unlinks any move: every move with a positive demand gets its quantity set to the demand and is marked `picked`, so `_action_done` validates it; zero-demand moves are left to `_action_done`, which cancels them. Tests now assert the receipt state, the received quantity on the purchase line and the stock on hand (standard flow, partially entered quantity, zero quantity, 2-step reception, invoice posting).
- **Priority re-evaluated:** P1 confirmed, impact larger than first described (verification 2026-10-01). In Odoo 19 supplier receipts bypass reservation and `_action_assign` sets the full quantity at confirmation, so in the standard flow *every* receipt move had `quantity == demand` and was deleted on `action_post` of the vendor bill: nothing was received. Even the kept branch was broken, because the moves were not marked `picked` and stayed `assigned`. Where a receipt move is chained to a later operation (`move_dest_ids`), `unlink` raised a UserError and blocked posting the bill.
- **Location:** `models/purchase.py`, `receipt_to_stock()`, lines 34–38.
- **Trigger:** Run automatic receipt on an assigned picking whose stock moves already have a reserved or entered quantity.
- **Actual behavior:** The method only keeps moves with a positive demand and zero `quantity`. Every other move is unlinked, including a legitimate move with demand 5 and quantity 5.
- **Example:** Isolated execution deleted a 5-unit assigned move before calling picking validation.
- **Impact:** Expected receipt lines can disappear, so products are not received as intended.
- **Evidence:** Executed the existing method with a mocked assigned picking. In Odoo 19, move quantity is computed from stock move line quantities, including assigned quantities. The current module test does not assert the resulting stock quantity.
- **Suggested fix:** Retain valid positive-demand moves, preserve or deliberately adjust existing quantities, and handle zero-demand lines separately.
- **Validation needed:** Automatic receipt with zero, fully reserved, partially entered, and fully entered quantities; assert actual received stock.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. RECEIPT-001 was fixed on 2026-10-01 with database-backed tests (`tests/test_receipt.py`).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **RECEIPT-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

## RECEIPT-002 — P1: Negative purchase lines access a nonexistent stock move UoM field

- **Status:** Fixed in 19.0.2.0.3. The loops read `move.product_uom`; the already returned quantity now adds the outgoing (return) moves and subtracts the incoming ones (the former signs were inverted, hidden by the error). Covered by `test_return_moves_count_existing_returns`.
- **Location:** models/purchase.py, PurchaseOrderLine._prepare_stock_moves().
- **Trigger:** Recompute negative purchase-line stock moves after at least one incoming or outgoing stock move exists.
- **Actual behavior:** The quantity accumulation loops read move.product_uom_id. Native Odoo 19 stock.move declares product_uom instead.
- **Impact:** The return computation raises AttributeError, preventing further stock-move creation for that line.
- **Evidence:** Executed the actual method with a native-shaped existing move containing product_uom: AttributeError for product_uom_id. Checked native fields and broad custom/Enterprise definitions; no restoring stock.move field found.
- **Suggested fix:** Use stock.move.product_uom and compare each move quantity in the purchase-line unit through native conversion.
- **Validation needed:** Existing incoming/outgoing moves, repeated quantity edits, differing units and cancelled moves.

## RECEIPT-003 — P1: Purchase-unit propagation loses the return move unit

- **Status:** Fixed in 19.0.2.0.3. The move template carries `product_uom` from `_adjust_uom_quantities()`. Covered by `test_return_keeps_purchase_unit` and `test_return_converted_to_product_unit`.
- **Location:** models/purchase.py, PurchaseOrderLine._prepare_stock_moves(), template and _adjust_uom_quantities result.
- **Trigger:** Set stock.propagate_uom to 1 and create a negative purchase line in Dozens for a product based in Units.
- **Actual behavior:** The native helper retains the purchase UoM and its numeric quantity, but the addon drops product_uom from the new move template. Native stock.move defaults its UoM to the product base unit. A return of 2 dozens therefore requests 2 Units instead of 24.
- **Impact:** Supplier returns move the wrong physical quantity when propagated purchase units differ from stock units.
- **Evidence:** Actual method execution with the helper contract qty 2/UoM Dozen returned demand 2 with no product_uom field. Traced native stock/models/product.py _adjust_uom_quantities and stock.move _compute_product_uom. No database return validation.
- **Suggested fix:** Include the returned product_uom in the stock move values, preferably using the native _prepare_stock_move_vals contract for shared attributes.
- **Validation needed:** propagate_uom enabled/disabled, Units/Dozens, fractional quantities and return stock/accounting effects.

## RECEIPT-004 — P2: Batch return-picking creation calls a singleton helper on the whole batch

- **Status:** Fixed in 19.0.2.0.3. `_create_picking()` uses `order` for the return operation type, locations and supplier. Covered by `test_create_return_pickings_for_several_orders`.
- **Location:** models/purchase.py, PurchaseOrder._create_picking().
- **Trigger:** Approve two purchase orders together, with a negative storable line requiring a return picking on at least one order.
- **Actual behavior:** Inside for order in self, the return values use self._get_destination_location(), self.picking_type_id and self.partner_id instead of order. The native destination helper starts with ensure_one.
- **Impact:** Batch approval raises Expected singleton and rolls back instead of creating the return transfers. Different partners or operation types also cannot safely share the batch-level values.
- **Evidence:** Traced native purchase_stock.button_approve into the multi-record _create_picking override. Inspected native _get_destination_location ensure_one and the exact addon call using self. No database batch approval.
- **Suggested fix:** Build every return using the current order record and retain its company, partner, type and location context.
- **Validation needed:** Two negative orders, one negative plus one positive order, differing suppliers, warehouses and companies.

### Additional review limitations — 2026-10-03

Integrated source review traced receipt/refund/replenishment and fast-purchase callers through current native Odoo contracts. Isolated actual-method checks: audit_coverage/reproductions/purchase_return_contracts.py. Database stock/valuation/accounting workflows were not executed; no fixes applied. The refund helper balance overwrite remains an unconfirmed candidate because native tax synchronization may repair it. Fast Purchase and Invoice Receipt define independent non-super receipt_to_stock implementations, so their combined method resolution requires an installed-module integration check.
