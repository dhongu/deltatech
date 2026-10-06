# Known bugs

Review date: 2026-10-03. Target version: Odoo 19.

## STOCKACCOUNT-001 — P1: Category account propagation and parent onchange read removed fields

- **Status:** Open.
- **Location:** models/product_category.py, write(), propagate_account(), _onchange_parent_id().
- **Trigger:** Set a category stock valuation account, run Propagate Accounts with an existing valuation account, or select a parent category.
- **Actual behavior:** Propagation accesses property_account_creditor_price_difference_categ and the stock input/output category accounts. Parent onchange also reads the removed input/output fields. Odoo 19 category defines property_price_difference_account_id instead of the old price-difference field and no longer declares those input/output fields.
- **Impact:** Saving the valuation-account change raises AttributeError and rolls back; propagation and the parent-selection flow fail.
- **Evidence:** Full module read traced write to propagate_account, plus local stock_account/models/product.py category definitions. Broad Python declaration search across Community, Enterprise, custom addons and customer trees found no field definitions restoring the three old fields. The module depends only on stock_account. No database onchange or category write executed.
- **Suggested fix:** Port category propagation to the actual Odoo 19 accounting fields and define which parent settings should propagate in the new valuation model. Preserve company-dependent values and test the effect of recursive writes.
- **Validation needed:** New and existing categories, selecting a parent, changing the valuation account, propagating to descendants and two-company account configurations.

## Review limitations

Full eligible source and native price/valuation dispatch inspected. The stale new_price parameter name in the product cost override is not a bug: it receives and forwards the native old-price dictionary unchanged. No posting or ORM integration tests executed; no fixes applied.
