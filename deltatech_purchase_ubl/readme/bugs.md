# Identified bugs

Reviewed: 2026-10-01
Target version: Odoo 20.0
Scope: Source review and isolated method validation. Integration-test results are reported separately below when available.

## [P1] An explicit zero-percent source tax is ignored

**Status:** Open — documented, not fixed.

**Location:** `models/purchase_invoice_import_mixin.py:553–558`. Line numbers refer to the reviewed source and may change.

### Cause

The truth-value check if product and tax_pct treats an explicitly declared 0% tax as missing. The method returns without changing the bill taxes when all source rates are zero.

### Impact

A generated bill can retain the nonzero purchase tax inherited from the order/product even though the source invoice explicitly declares 0%.

### Reproduction

Import a source line with tax_percent=0 for a purchase order whose line has a nonzero purchase tax. Create the bill and inspect its taxes.

### Recommended correction

Distinguish a missing tax percentage from an explicit zero in the parser and the tax application method. Resolve the appropriate zero/exempt tax rather than retaining the nonzero default.

### Validation

Confirmed with real ORM records in the isolated audit database: a draft bill with a 21% purchase tax retained 21% after applying source tax_percent=0.0. The audit transaction was rolled back. The existing test test_apply_xml_taxes_to_bill_noop_without_tax_percent also passes 0 as if it meant absence, so it preserves this behavior rather than testing an explicitly zero-rated invoice.

## [P1] Updating a supplier price can overwrite another product variant

**Status:** Open — documented, not fixed.

**Location:** `models/purchase_invoice_import_mixin.py:407–424`. Line numbers refer to the reviewed source and may change.

### Cause

The supplierinfo search filters by partner and product template only. It can select a record linked to another variant, then write product_id to the currently imported variant.

### Impact

Importing variant B can repurpose variant A supplier record, removing A vendor code/price and replacing it with B data.

### Reproduction

Create variants A and B under one template and a supplierinfo linked to A. Import a source line mapped to B with update_prices enabled. The existing A supplierinfo is found and rewritten with product_id=B.

### Recommended correction

Match supplierinfo by the imported variant, with a deliberate policy for template-level records, and scope to company/currency where appropriate. Create a new variant record rather than converting a sibling record.

### Validation

Confirmed with real ORM records in the isolated audit database: two variants shared a template and one supplierinfo belonged to A. After calling the helper for B, the same supplierinfo belonged to B and the supplier still had only one price record. The audit transaction was rolled back.

## [P1] Duplicate product lines receive the last source quantity on every move

**Status:** Open — documented, not fixed.

**Location:** `models/purchase_invoice_import_mixin.py:718–719 and :483–487`. Line numbers refer to the reviewed source and may change.

### Cause

The receipt map is keyed only by product ID, so later source lines overwrite earlier quantities. Receipt validation then applies that same product quantity independently to every matching stock move.

### Impact

Two invoice lines for the same product can validate an incorrect received quantity and affect inventory and receipt-based vendor billing.

### Reproduction

Use two source lines for the same product with quantities 2 and 3, and a receipt with two corresponding moves. The map keeps 3, and both moves are assigned 3, giving 6 received instead of 5.

### Recommended correction

Preserve source-to-order-line/move identity and distribute quantities accordingly. Simply summing by product is insufficient if the summed amount is subsequently applied to every move.

### Validation

The actual map comprehension and receipt validation method were executed in isolation. The map was {product_id: 3} and the two move quantities became [3, 3].

## [P1] Source quantities and unit prices are applied without unit conversion

**Status:** Fixed in 20.0.1.4.4 (UBL-005) — `_process_invoice_data()` resolves the source unit of every line (`_source_uom()`, no fallback for unknown codes) and `_convert_source_line()` converts quantity/price to the existing order line unit; new order lines keep the source unit when compatible with the product unit; the receipt map is expressed in the product unit and converted to each move unit (`_receipt_qty_in_move_uom()`); `_update_supplier_price()` converts the price to the unit of an existing vendor row or creates the new row in the source unit. Incompatible units are not converted and are reported in the log. Port of 19.0.1.4.4 (dhongu/deltatech#3118). Covered by tests in tests/test_ubl_import_uom.py.

**Location:** `models/purchase_invoice_import_mixin.py:670–675 and :689–695`. Line numbers refer to the reviewed source and may change.

### Cause

Existing order lines receive raw source qty and price while retaining their unit. New lines use product.uom_id regardless of the source unit_code. The unit-code helper is used for creating missing products, but not for quantities of existing matched products.

### Impact

A source invoice in kilograms can be imported as the same numeric quantity in grams when the matched product/order uses grams, producing incorrect stock quantities and per-unit prices.

### Reproduction

Match an existing product measured in grams to a source line with unit_code=KGM, qty=1 and price=10 per kilogram. A new purchase line receives quantity 1 in grams and price 10 per gram rather than 1000 grams at 0.01 per gram.

### Recommended correction

Resolve the source unit and convert both quantity and unit price to the destination purchase-line unit. Reject incompatible units instead of silently reusing raw numbers.

### Validation

The existing-line writes, new-line unit assignment and unit-code helper callers were traced in source. A database scenario for cross-unit imports remains to be run.

## [P1] Source currency is not validated against the matched order currency

**Status:** Open — documented, not fixed.

**Location:** `models/purchase_invoice_import_mixin.py:673–675, :168 and :579–590`. Line numbers refer to the reviewed source and may change.

### Cause

The import writes raw source prices into the order without checking or converting the source currency. The bill is created from the order currency, and the total check compares raw numeric amounts and labels them with the order currency.

### Impact

A RON source invoice matched to an EUR purchase order can turn a numeric RON price into the same numeric EUR price and produce a bill in the wrong currency. Equal numbers can also pass the total check despite different currencies.

### Reproduction

Match a RON source invoice to an EUR purchase order. Import a source unit price of 100 and inspect the order price and bill currency. The raw 100 is applied in EUR.

### Recommended correction

Validate the document/order currency before changing lines. Either require a matching currency or implement explicit conversion and bill-currency handling using the document date; make the total check currency-aware.

### Validation

The source currency data, order-price writes, native bill creation and total-check formula were compared in source. No exchange-rate data or production bill was modified.

## [P1] Duplicate bill lookup is not scoped to the order company

**Status:** Open — documented, not fixed.

**Location:** `models/purchase_invoice_import_mixin.py:538–545 and :739–745`. Line numbers refer to the reviewed source and may change.

### Cause

_find_duplicate_bill() searches by vendor and reference without company_id. When multiple companies are active, their bills can be visible to the same user.

### Impact

A bill from company A can be treated as the duplicate for an import into company B, suppressing creation of B bill and setting the wizard bill_id to A document.

### Reproduction

Allow companies A and B, use a shared supplier and an existing A bill with reference INV-1. Import INV-1 against an order belonging to B. The duplicate domain can return the A bill.

### Recommended correction

Pass the resolved order/company into the duplicate lookup and include that company explicitly in the search domain.

### Validation

Confirmed with real ORM records in the isolated audit database: company A was current, both A and B were active, and the matching bill belonged to B. The lookup returned the B bill without restricting the result to A. The audit transaction was rolled back.

## [P2] A prepaid invoice is compared using amount due instead of invoice total

**Status:** Open — documented, not fixed.

**Location:** `models/purchase_invoice_import_mixin.py:154–168`. Line numbers refer to the reviewed source and may change.

### Cause

The total check prefers payable_amount over tax_inclusive_amount, then compares it to the full purchase order amount_total. Payable amount can be reduced by prepayments.

### Impact

A correctly matched prepaid invoice is flagged as a total mismatch and can unnecessarily trigger the unattended-import warning workflow.

### Reproduction

Use an order total of 100 and source tax_inclusive_amount=100, payable_amount=60 after a prepayment of 40. The method reports a difference of 40 even though the invoice total matches.

### Recommended correction

Compare like amounts: use the invoice gross total for the order-total check and validate outstanding/payable amounts separately.

### Validation

The actual total-check method was executed in isolation with these values and returned matches=False and difference=40.

## Integration validation

On 2026-10-01, the existing module test suite ran in the separate test20_bug_audit_20261001 database: 39 tests completed with zero failures and zero errors. Passing these tests does not cover all findings above. Separate ORM reproductions confirmed the zero-tax, supplier-variant and cross-company duplicate issues; all reproduction records were rolled back. Other findings retain their individual validation limits.
