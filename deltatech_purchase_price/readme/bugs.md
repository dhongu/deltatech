# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## PURCHASEPRICE-001 — P1: Automatic sale-price updates use the user's default company currency

- **Status:** Fixed in 19.0.1.2.11 — `ProductTemplate.onchange_last_purchase_price()` takes the source currency and the conversion company from `self.env.company` (the company set by `with_company()` in `update_last_purchase_price()`, the same one the company-dependent `last_purchase_price` is read in) instead of `self.env.user.company_id`. Covered by tests in `tests/test_multi_company.py` (supplier price in company B, onchange with active company B).
- **Location:** `models/product.py`, `ProductTemplate.onchange_last_purchase_price()`, the currency/company assignments before the product loop.
- **Trigger:** Enable `purchase.update_list_price`, run a supplier-price update in company B, and use a user whose default company A has a different currency. The supplier update explicitly calls `with_company(B)` before the onchange.
- **Actual behavior:** The onchange reads `self.env.user.company_id` for the source currency and conversion company instead of the active company established by `with_company()`. A purchase cost expressed in company B currency is treated as company A currency.
- **Example:** In an isolated reproduction, company B cost 100 EUR with a 100% markup became 40 EUR instead of 200 EUR because company A used RON and the conversion rate was 5 RON/EUR.
- **Expected behavior:** Company B's purchase cost and company currency remain the basis for its price update.
- **Impact:** Automatic updates can write materially incorrect sale prices in multi-company deployments.
- **Evidence:** Executed the existing template onchange with different default and active companies; source inspection confirmed that supplier updates use `with_company()` before invoking it.
- **Suggested fix:** Use the active/record company consistently for source currency and conversion, aligned with the company-dependent purchase price.
- **Validation needed:** Supplier updates in both companies with different currencies, switching active company while retaining the same user's default company.

## PURCHASEPRICE-002 — P1: Forced supplier-price updates access the removed product_uom field

- **Status:** Open.
- **Location:** models/purchase.py, button_confirm(); models/account_move.py, action_post().
- **Trigger:** Enable purchase.force_price_at_validation and confirm a PO with a matching supplier pricing row, or post a vendor bill whose line unit differs from the product default.
- **Actual behavior:** PO confirmation compares/uses line.product_uom, while Odoo 19 purchase.order.line defines product_uom_id. Vendor bill posting correctly checks product_uom_id but then converts through line.product_uom, also absent on account.move.line.
- **Evidence:** Complete hooks read and compared local core field declarations in purchase_order_line.py and account_move_line.py. Both define product_uom_id; the old attribute remains in the active forced-price paths. No PO confirmation or bill posting executed.
- **Impact:** AttributeError aborts and rolls back confirmation/posting with forced-price updates enabled. The bill path is triggered by differing units; the PO comparison accesses the missing field even before conversion.
- **Suggested fix:** Use product_uom_id consistently and convert to the actual supplier pricing unit rather than assuming the product default unit.
- **Validation needed:** Enabled/disabled setting, same/different PO and invoice units, matching supplier entries and converted supplier prices; normal confirmation/posting must complete.

## Review limitations

Verified through local source and dependency analysis and the isolated reproductions stated above. Fresh-database installations and database-backed integration tests have not been run. No fixes have been applied.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **PURCHASEPRICE-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
