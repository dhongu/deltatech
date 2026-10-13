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

## Integrated review — 2026-10-03

SALEEXTRA-001 remains fixed in current source: flag-based ownership, product reconciliation and extra-line recursion skip retained. Complete source including migrations read; native website cart hooks call the new verification hook after add/quantity update. Native standard price fields/manual-price semantics and view anchors checked. Historical database tests not rerun.

### SALEEXTRA-002 — P2: pallet addon replaces the same onchange

This addon and deltatech_sale_pallet both implement sale.order.onchange_order_line with @api.onchange("order_line"), and neither chains super(). Native models._onchange_methods (:561–593) uses getmembers on the effective registry class: only the final method for this attribute is registered, not every same-name implementation in the MRO. With both installed, one module's order-line generation is lost in the form: either extra products stop synchronizing or pallet quantities stop synchronizing, depending on load order. Rename the callbacks or chain the existing method consistently. Website cart extra synchronization has a separate hook and is not automatically affected.

Evidence: both full module sources and native callback registry read. No installed-registry/form test executed; the collision is independent of which implementation wins.

### Limits

The migration classifies the larger ID of exactly two UUID-paired lines as extra; legacy/imported ID ordering is a migration validation limit, not a confirmed failure without actual affected rows. No general create/write synchronization is provided by sale addon; form/cart are documented entry points, so direct RPC omission is not separately asserted here.
