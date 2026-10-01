# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PURCHASEEXTRA-001 — P2: Changing the main product keeps the old automatic extra product

- **Status:** Open.
- **Location:** models/purchase.py, write(), check_extra_product(), and unlink().
- **Trigger:** Create a draft RFQ with product A configured to add extra product X, then replace A with product B configured to add Y, or with a product that has no extra.
- **Actual behavior:** The saved product_id change invokes check_extra_product(), but an existing paired line is identified only by UUID. Its quantity/price can change, while its product_id and UoM are never replaced with Y. If B has no extra, the function skips the line and leaves X; deleting B also skips paired-line cleanup because B has no extra configuration.
- **Evidence:** Executed the actual method extracted from its AST with a paired X line and a new main product configured for Y: the quantity changed to 6 while product_id remained X (10) instead of Y (20). Inspected the no-extra and deletion guards.
- **Impact:** RFQs can retain and order an unrelated product or service after the main item is changed.
- **Suggested fix:** Reconcile the existing pair with the current extra product, replacing its product/UoM and resetting generated pricing when necessary; remove generated pairs when the main product no longer requires them. Track ownership independently of current product configuration.
- **Validation needed:** Change main A/X to B/Y, change to a product with no extra, then delete the main line; cover manual extra prices and both live forms and ORM writes.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
