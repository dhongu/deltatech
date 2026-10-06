# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PURCHASEEXTRA-001 — P2: Changing the main product keeps the old automatic extra product

- **Status:** Fixed in 19.0.1.4.0. The generated extra lines are now marked with the new field `is_extra_line`, which a migration sets on the pairs created by older versions (in a pair, the extra line is the one with the higher id). `check_extra_product()` checks the extra line against the current extra product. If the products differ, or the new product has no extra, the old line is removed and, when needed, a new extra line is generated with the new product's UoM, quantity and computed price. A manual price on the old line is not carried over, because it belonged to another product. The live form gets the obsolete lines back from `check_extra_product()` and drops them from `order_line`. `unlink()` finds the pair through `is_extra_line`, not through the product configuration, and skips lines that are already deleted. `purchase.order.write()` synchronizes the lines only after all the one2many commands are applied, so a form save does not create the new extra twice. Extra lines are never treated as main lines. Covered by 6 tests in `tests/test_purchase.py`: ORM write and form, replacing B/Y and switching to a product without an extra, unlink without an extra configuration, and an extra product that has its own extra.
- **Location:** models/purchase.py, write(), check_extra_product(), and unlink().
- **Trigger:** Create a draft RFQ with product A configured to add extra product X, then replace A with product B configured to add Y, or with a product that has no extra.
- **Actual behavior:** The saved product_id change invokes check_extra_product(), but an existing paired line is identified only by UUID. Its quantity/price can change, while its product_id and UoM are never replaced with Y. If B has no extra, the function skips the line and leaves X; deleting B also skips paired-line cleanup because B has no extra configuration.
- **Evidence:** Executed the actual method extracted from its AST with a paired X line and a new main product configured for Y: the quantity changed to 6 while product_id remained X (10) instead of Y (20). Inspected the no-extra and deletion guards.
- **Impact:** RFQs can retain and order an unrelated product or service after the main item is changed.
- **Suggested fix:** Reconcile the existing pair with the current extra product, replacing its product/UoM and resetting generated pricing when necessary; remove generated pairs when the main product no longer requires them. Track ownership independently of current product configuration.
- **Validation needed:** Change main A/X to B/Y, change to a product with no extra, then delete the main line; cover manual extra prices and both live forms and ORM writes.

## Review limitations

The findings were based on local source inspection and the isolated reproductions stated above. The fix of PURCHASEEXTRA-001 is covered by database-backed tests in `tests/test_purchase.py`, and the migration was checked on a database populated with the previous version.

## Historical local-checkout reverification — 2026-10-01

Historical snapshot: compared the then-current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PURCHASEEXTRA-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.

The historical checkout result above is tied to its stated commit. It does not override the current status in this report or establish that a locally observed fix exists on the published branch. Remote documentation and fixes were preserved during publication on 2026-10-02.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PURCHASEEXTRA-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.

## Integrated review — 2026-10-03

PURCHASEEXTRA-001 remains open: product replacement and no-extra configuration do not reconcile/remove the old pair. Full eligible source, migrations, native purchase price/manual-price contracts and view anchors reviewed. Historical isolated reproduction not rerun.

### PURCHASEEXTRA-002 — P2: cyclic extra-product configuration recurses during creation

The extra_product_id field has no constraint against self-reference or cycles. create() invokes check_extra_product() on every created line; that method creates another line before assigning the main line's UUID. Configure A.extra_product_id = A (or A→B→A), then create an RFQ line for A. Every newly generated line enters the same create hook, has no existing pair and creates another. The write recursion guard does not guard create. Creation cannot finish normally and rolls back upon recursion/resource failure. Skip generation for marked extra lines and validate cycles.

Evidence: complete actual create/check call chain and unrestricted product field traced; source proof only, no database recursion deliberately executed. Acyclic chained extras can also overwrite UUID pairing, but not asserted as a separate defect without a defined chaining policy.

### Limits

Raw SQL migration is constant, not an injection issue. Shared product configuration declarations match the sale addon. NewId order inverse links were previously traced in native ORM and are not assumed missing here. Manual-price logic compared with native technical_price_unit behavior; no new manual-price defect asserted. No database/form tests executed.
