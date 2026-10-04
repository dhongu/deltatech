# Bug review — deltatech_purchase_xls

Review date: 2026-10-02. Target version: Odoo 19.

## PURCHASEXLS-001 — P1: Supplier product codes are matched without the order vendor or company

- **Status:** Fixed in 19.0.1.0.2 — `search_product()` filters `product.supplierinfo` on `partner_id child_of` the commercial partner of the order vendor and `company_id in [order company, False]`, collects the products of all matching rows (variant or all template variants) and raises a `UserError` when more than one product matches; the `default_code` fallback is filtered on the order company; `create_product()` sets `company_id` on the new vendor pricing row. Covered by tests in `tests/test_search_product.py` (two vendors with the same code, vendor contact, order company, code of another vendor only, ambiguous code).
- **Location:** wizard/import_purchase_line.py, search_product().
- **Trigger:** Two suppliers use the same product_code for different products, or that code appears in different companies.
- **Actual behavior:** The first product.supplierinfo row matching product_code is selected under sudo without partner_id, company_id or variant applicability. The purchase order vendor is not consulted. The resulting product can belong to another supplier configuration.
- **Evidence:** Executed the actual method extracted by AST for an order vendor 20/company 2: the only search domain is product_code=SKU and it returns mock product 99 from the first supplier row. No live supplier records read.
- **Impact:** Imported purchase lines can order the wrong physical product for a supplier code and use otherwise inaccessible company-specific supplier configuration.
- **Suggested fix:** Scope supplier code resolution to the order vendor/commercial partner and company, validate variant ambiguity, and apply internal-code fallback explicitly.
- **Validation needed:** Same code across vendors/companies, variant-specific suppliers and ambiguous matches; selected product must belong to the applicable supplier mapping.

## PURCHASEXLS-002 — P2: Standard purchase-line imports fail without a context order

- **Status:** Fixed in 19.0.1.0.4 — `_get_import_order()` takes the order from the context or from the `order_id`, `order_id/id` or `order_id/.id` column (at any index, resolved by name, external id or database id) only when all the rows point to one existing order; otherwise the rows go to the standard import unchanged. Covered by `test_load_without_order_context` and the `test_load_order_column_*` tests.
- **Location:** models/purchase_order.py, PurchaseOrderLine.load().
- **Trigger:** Import purchase.order.line records using standard CSV import without default_order_id or active_id in context.
- **Actual behavior:** The no-context-order branch calls fields.index.get("order_id", False), but fields is a Python list and fields.index is a method with no get attribute. This executes before the superclass importer, including when the CSV contains a valid order_id column.
- **Evidence:** Executed the actual AST-extracted override with fields=[order_id,product_id] and empty context: AttributeError, builtin_function_or_method has no attribute get. Mock environment only.
- **Impact:** Installing this addon breaks otherwise valid general purchase-line imports outside its order-specific action.
- **Suggested fix:** Use supported field-path parsing or let the native importer handle rows without an explicit single-order context; do not assume one order for a multi-order dataset.
- **Validation needed:** General imports with order_id/order_id:id, multi-order rows, no order column and the order-specific line action.

## PURCHASEXLS-003 — P2: Exported rows without supplier codes are silently skipped on reimport

- **Status:** Open.
- **Location:** wizard/export_purchase_line.py, do_export(); wizard/import_purchase_line.py, do_import().
- **Trigger:** Export a purchase line whose product has an internal code but no product_code on a matching supplier entry, then reimport with the default six-column mapping and Search by internal code enabled.
- **Actual behavior:** Export places an empty supplier code in column one and the internal code in column two. Import unconditionally skips rows without product_code before considering default_code; it never reads the default_code column at all. Search by internal code only changes lookup of column one.
- **Evidence:** Executed actual AST-extracted export using xlsxwriter and read its bytes with openpyxl: row [empty,INT001,Widget,2,10,Units]. Passing that row to the actual import method with default mapping creates zero lines without an error. Mock ORM only; no Odoo workbook import executed.
- **Impact:** The module cannot round-trip common purchase lines and silently drops products despite exporting their internal references.
- **Suggested fix:** Resolve supplier code and internal code as distinct fields, allow internal-code fallback when the supplier code is empty, and report skipped/unresolved rows.
- **Validation needed:** Round-trip products with only internal codes, only supplier codes, both codes and neither, with Search by internal code enabled/disabled.

## PURCHASEXLS-004 — P2: Removing import rows during iteration skips validation of following rows

- **Status:** Fixed in 19.0.1.0.4 — `load()` builds a new list of rows instead of removing rows from the list being iterated; rows of products with several lines on the order are matched to the first line not used yet. Covered by `test_load_existing_lines_consecutive_dropped_rows*` and `test_load_existing_lines_same_product`.
- **Location:** models/purchase_order.py, PurchaseOrderLine.load().
- **Trigger:** Update an existing order through line import with two consecutive rows for unknown products or products not already on the order.
- **Actual behavior:** The override removes record from data inside for record in data. The following row shifts into its position and is skipped, so a row that should be excluded reaches the native importer with an empty .id. It can create an unintended new line or make the whole import fail.
- **Evidence:** Executed the actual override with rows Unknown A, Unknown B, Known: Unknown A is removed but Unknown B remains; Known receives existing line ID 10. Superclass mock receives [[Unknown B,empty],[Known,10]]. No native import/database write executed.
- **Impact:** Filtering is inconsistent and depends on row order. Unsupported new-product rows can bypass the update-only matching behavior or prevent valid updates.
- **Suggested fix:** Construct a separate validated output list instead of removing rows while traversing it, and report excluded rows explicitly.
- **Validation needed:** Consecutive/interleaved unknown and absent-order products, all invalid rows and duplicate products; only validated intended updates should reach load.

## Review limitations

All eligible source was manually read. Actual-method reproductions use mocked ORM objects; the export workbook was generated/read in memory only. No Odoo database imports, purchase mutations or integration tests executed.
