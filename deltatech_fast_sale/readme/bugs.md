# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## FASTSALE-001 — P2: Delivery notice crashes when more than one transfer is selected

- **Status:** Open.
- **Location:** models/sale.py, action_button_confirm_notice().
- **Trigger:** Use Deliver Notice on a sale order with at least two assigned transfers.
- **Actual behavior:** pick_ids is set to picking_ids.ids, a Python list. The multiple-transfer domain then interpolates pick_ids.ids, which does not exist.
- **Impact:** The action fails with AttributeError instead of opening the transfers; notice flag writes in the failed transaction roll back.
- **Evidence:** Executed the actual method with two assigned pickings: list.ids AttributeError. Existing tests exercise one picking only.
- **Suggested fix:** Use the identifier list directly in a structured action domain.
- **Validation needed:** One/multiple assigned transfers, no assigned transfers and notice flags after successful/failed actions.

## FASTSALE-002 — P2: Multi-step delivery is rejected before the upstream stock movement runs

- **Status:** Open.
- **Location:** models/sale.py, _prepare_pickings(), action_button_confirm_to_invoice().
- **Trigger:** Use Confirm, Deliver and Invoice in a two-step delivery warehouse with stock in WH/Stock but none yet in WH/Output.
- **Actual behavior:** The helper attempts to reserve every unfinished picking and demands every move already be assigned before any picking is completed. The downstream chained delivery needs the upstream pick to finish first, so it remains waiting and the helper raises Not all products are available.
- **Impact:** The combined sale flow is blocked despite enough stock at the start of the configured route.
- **Evidence:** Traced native stock.move._action_assign and _get_available_move_lines_in: downstream availability comes from done ancestor move lines. Actual helper execution with an assigned upstream step and waiting downstream step raises before any upstream execution. Synthetic reservations confirm control flow; no two-step database delivery executed.
- **Suggested fix:** Execute and verify route steps in their dependency order, reserving downstream stock after upstream completion. Preserve normal stock/tracking/backorder checks.
- **Validation needed:** One/two/three-step routes, available/missing stock, tracked products and repeated partial deliveries.

## Review limitations

Full eligible source and native sale/stock/invoice contracts inspected. Actual-method reproductions: audit_coverage/reproductions/fast_sale_currency.py. No database delivery, invoice posting or browser execution. Missing active_ids in the returned invoice action was excluded: native object-button action handling merges the active record context. Downpayment currency hook matches native recomputation structure; no further concrete defect asserted there. No fixes applied.
