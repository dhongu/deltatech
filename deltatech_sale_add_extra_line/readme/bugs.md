# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## SALEEXTRA-001 — P2: Changing the main product keeps the old automatic extra product

- **Status:** Open.
- **Location:** models/sale.py, SaleOrderLine.check_extra_product() and unlink().
- **Trigger:** On a quotation with a main product A and generated extra X, change the main product to B which requires extra Y, or to a product with no extra, then synchronize the lines.
- **Actual behavior:** The existing extra is found by UUID, but its product is not checked against _get_extra_product(). Only quantity/price are updated. When the new product has no extra, the existing generated line is left behind and unlink also skips its cleanup.
- **Evidence:** Executed the actual method extracted from its AST with a paired X line and main product B configured for Y: quantity became 6 while product_id stayed X (10) rather than Y (20). Inspected the absent-extra branch and unlink guard.
- **Impact:** Quotations can charge or deliver an unrelated extra product after a main-line product change.
- **Suggested fix:** Reconcile generated lines with the current extra product and remove obsolete pairs. Preserve deliberate manual prices only where the paired product remains the same.
- **Validation needed:** Backend product replacement, replacement with no-extra product, subsequent deletion, manual prices, and synchronization through the cart hook.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
