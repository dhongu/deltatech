# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEEXTRA-001 — P2: Changing the main product keeps the old automatic extra product

- **Status:** Fixed in 19.0.1.5.0. The generated line is flagged with the new technical field `is_extra_line` and paired with its main line through `_get_extra_line()` (same UUID + flag), so the pair no longer depends on the current product configuration. `check_extra_product()` skips extra lines, removes the paired line when its product differs from `_get_extra_product()` or when there is no extra product any more, and regenerates the right one with the computed price (a manual price belonged to the old extra product and is not carried over; it is still kept while the extra product stays the same). `unlink()` removes the flagged pair whatever the product configuration, and no longer recurses when the extra product has an extra product of its own. A migration flags the existing extra lines (the line created last of each UUID pair). Covered by tests on the form, the ORM and the cart hook.
- **Location:** models/sale.py, SaleOrderLine.check_extra_product() and unlink().
- **Trigger:** On a quotation with a main product A and generated extra X, change the main product to B which requires extra Y, or to a product with no extra, then synchronize the lines.
- **Actual behavior:** The existing extra is found by UUID, but its product is not checked against _get_extra_product(). Only quantity/price are updated. When the new product has no extra, the existing generated line is left behind and unlink also skips its cleanup.
- **Evidence:** Executed the actual method extracted from its AST with a paired X line and main product B configured for Y: quantity became 6 while product_id stayed X (10) rather than Y (20). Inspected the absent-extra branch and unlink guard.
- **Impact:** Quotations can charge or deliver an unrelated extra product after a main-line product change.
- **Suggested fix:** Reconcile generated lines with the current extra product and remove obsolete pairs. Preserve deliberate manual prices only where the paired product remains the same.
- **Validation needed:** Backend product replacement, replacement with no-extra product, subsequent deletion, manual prices, and synchronization through the cart hook.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. SALEEXTRA-001 was then reproduced and verified with database-backed tests (`tests/test_sale.py`, `tests/test_website_cart.py`).

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **SALEEXTRA-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.
