# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## UBL-001 — P1: Explicit zero VAT is ignored when creating the vendor bill

- **Status:** Open.
- **Location:** models/purchase_invoice_import_mixin.py, _apply_xml_taxes_to_bill(); wizard/ubl_import_wizard.py, line tax parsing.
- **Trigger:** Import a line whose UBL tax Percent is 0, while the matched purchase/bill line has a nonzero default supplier tax (for example 21%).
- **Actual behavior:** The parser returns numeric 0.0, but the tax override only records truthy tax_percent values. It returns without overriding that line, leaving the nonzero default tax.
- **Evidence:** Executed the actual tax override extracted from its AST with tax_percent=0.0 and an existing 21% tax: the original tax IDs remained and no tax search occurred. Verified that UBL Percent is parsed numerically.
- **Impact:** The vendor bill can contain VAT not present on the supplier invoice, producing incorrect totals and tax entries.
- **Suggested fix:** Distinguish an explicit zero rate from a missing rate and apply the appropriate zero/exempt tax category or clear taxes according to the source document. Preserve exemption/category metadata where required.
- **Validation needed:** Explicit zero rate, absent Percent, a standard positive rate, exempt categories, and comparison with source tax totals.

## UBL-002 — P2: Different tax rates for the same product collapse to the last rate

- **Status:** Open.
- **Location:** models/purchase_invoice_import_mixin.py, _apply_xml_taxes_to_bill().
- **Trigger:** Import two lines mapped to the same product but carrying different source tax rates, such as 21% and 9%.
- **Actual behavior:** The override stores one percentage per product ID; the last source line overwrites earlier entries. It then applies that percentage to every invoice line for the product rather than matching each source line.
- **Evidence:** Executed the actual method with two invoice lines for the same product and source rates 21 and 9: both invoice lines received the 9% tax.
- **Impact:** The imported bill does not preserve line-specific VAT rates and can differ from supplier totals and tax breakdowns.
- **Suggested fix:** Maintain source-to-purchase/bill-line correspondence and apply each line tax/category independently; do not use product ID as the sole tax key.
- **Validation needed:** Repeated products with identical and different rates, multiple purchase lines, zero rates, and source/bill tax-total reconciliation.

## UBL-003 — P1: Repeated product lines produce incorrect received quantities

- **Status:** Open.
- **Location:** models/purchase_invoice_import_mixin.py, _process_invoice_data() receipt line_map and _validate_receipt_quantities().
- **Trigger:** Import two source lines for the same product with quantities 2 and 3 and enable receipt validation.
- **Actual behavior:** The dict keyed only by product ID retains the last quantity (3). The receipt helper assigns that entire quantity to every matching move. With two moves, the result is 3+3 instead of 2+3; if moves are merged, it receives 3 instead of the source total 5.
- **Evidence:** Built the exact product-to-quantity mapping used by the importer and executed the actual receipt helper with two matching moves: both quantities became 3, total 6. Inspected both receipt-helper branches, which use the same product-only lookup.
- **Impact:** Stock can be over-received or under-received, distorting stock availability, valuation, and receipt-based vendor billing.
- **Suggested fix:** Map quantities to the matched purchase/move lines with unit conversion, or aggregate by product/UoM and distribute the total across moves without duplicating it.
- **Validation needed:** Repeated product lines, merged/unmerged receipt moves, different line units, partial/backorder receipts, and verification that received totals match the document.

## UBL-004 — P2: Duplicate invoice detection can select another company bill

- **Status:** Open.
- **Location:** models/purchase_invoice_import_mixin.py, _find_duplicate_bill() and _process_invoice_data() bill creation.
- **Trigger:** A user can access companies A and B. A already has a vendor bill for a shared partner with reference REF; import a legitimate B invoice from that partner with the same reference.
- **Actual behavior:** The duplicate search filters partner/reference/type/state but not company. With both companies allowed, A bill can match; the importer sets bill_id to it and skips creating the B bill.
- **Evidence:** Executed the actual duplicate helper with an environment whose current company is B and a search returning an A record: the returned bill was A and the captured domain had no company clause. Inspected the caller, which skips creation when any duplicate is found. The mock verifies the domain and decision; no database cross-company search was run.
- **Impact:** A legitimate company-B import can be silently linked to company A and remain unbilled in B.
- **Suggested fix:** Pass the resolved order/invoice company into duplicate detection and include it in the search domain; use the same company context throughout import and billing.
- **Validation needed:** Same partner/reference in two allowed companies, one-company duplicates, cancelled bills, and an order company differing from the current environment.

## UBL-005 — P1: Import copies source quantities and prices without unit conversion

- **Status:** Fixed in 19.0.1.4.4 — `_process_invoice_data()` resolves the source unit of every line (`_source_uom()`, no fallback for unknown codes) and `_convert_source_line()` converts quantity/price to the existing order line unit; new order lines keep the source unit when compatible with the product unit; the receipt map is expressed in the product unit and converted to each move unit (`_receipt_qty_in_move_uom()`); `_update_supplier_price()` converts the price to the unit of an existing vendor row or creates the new row in the source unit. Incompatible units are not converted and are reported in the log. Covered by tests in tests/test_ubl_import_uom.py.
- **Location:** models/purchase_invoice_import_mixin.py, _process_invoice_data(), _update_supplier_price() and _validate_receipt_quantities().
- **Trigger:** A matched existing product/order line uses a different unit from the XML InvoicedQuantity unitCode, for example an order in kg and a source line for 1000 grams priced at 0.01 per gram.
- **Actual behavior:** Existing order lines receive the raw quantity and price while retaining their order unit. Newly added lines use product.uom_id regardless of source unit_code. Receipt moves receive the same raw quantity, and supplier prices are overwritten without setting/converting the supplier unit. Unit resolution is used only when creating a new product.
- **Evidence:** Complete processing source reviewed against local Odoo 19 stock.move quantity conversion and product.supplierinfo product_uom_id semantics. No source-to-target _compute_quantity/_compute_price call exists on these paths. In the example, the kg order receives product_qty=1000 and price_unit=0.01 instead of 1 kg at 10 per kg. No database receipt or bill executed.
- **Impact:** Imported orders and receipts can represent the wrong physical quantity, while vendor prices are stored for the wrong unit. Stock valuation and future purchases can be misstated even when the extended monetary amount coincidentally matches.
- **Suggested fix:** Resolve source units for every mapped line and convert quantities and unit prices to the destination order, supplier and move units independently; reject unsupported or ambiguous units.
- **Validation needed:** Grams/kg, individual units/packs, existing and newly added order lines, supplier units different from stock units, and exact received quantities.

## UBL-006 — P2: Supplier price update repurposes another variant's pricing row

- **Status:** Open.
- **Location:** models/purchase_invoice_import_mixin.py, _update_supplier_price().
- **Trigger:** A product template has variants A and B with separate supplier pricing records; import a price for B while the first matching supplier/template record belongs to A.
- **Actual behavior:** The search restricts supplier and template only, with limit=1. The chosen record is then overwritten with B's product_id, code, price and currency, removing its association with A. Company, quantity tiers and validity periods also do not participate in selecting the row.
- **Evidence:** Executed the actual method extracted through AST with a mock supplier row belonging to variant 10 and an import for variant 20. Captured search had no variant condition; the existing row became product_id=20 and price=80. Compared with local product.supplierinfo variant semantics. No real pricing data modified.
- **Impact:** Importing one variant can destroy the supplier code/price configuration for another variant and leave duplicate pricing entries for the imported variant.
- **Suggested fix:** Select a compatible variant and company-specific pricing row under an explicit tier/date policy; create a new row when no suitable record exists rather than changing an unrelated variant's identity.
- **Validation needed:** Two variants with separate codes/prices, shared template prices, company-specific records and quantity/date tiers; importing B must preserve A.

## UBL-007 — P3: Unit code SET maps to a non-existent XML ID and falls back to Units

- **Status:** Open. Found on 2026-10-03 while fixing UBL-005.
- **Location:** models/purchase_invoice_import_mixin.py, `_uom_from_code()` (`"SET": "uom.product_uom_set"`).
- **Trigger:** Import a UBL/PDF line with unit code SET.
- **Actual behavior:** `uom.product_uom_set` does not exist in Odoo 19 (`product_uom_set` is defined only by `l10n_tr_nilvera`, under that module's namespace). `env.ref(..., raise_if_not_found=False)` returns nothing, so new products are created in Units (`fallback=True`) and source-unit conversion treats SET as an unknown unit (`fallback=False`, no conversion, no warning).
- **Evidence:** source inspection of the mapping and search of the Odoo 19 `uom` data files; no import executed.
- **Impact:** Sets are silently handled as pieces; with a set unit configured on the product or order line the quantity and price are not converted. The mapping entry is dead code.
- **Suggested fix:** Remove the entry or map SET to an existing/configurable unit (for example by searching a unit of the Unit category named Set, or a configurable mapping), and report unknown codes in the import log.
- **Validation needed:** Import a SET line with and without a matching set unit; assert the chosen unit and the conversion.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **UBL-001 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **UBL-002 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **UBL-003 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
- **UBL-004 — still open:** no relevant Python, XML, JavaScript or manifest change since the audit snapshot; the documented implementation remains in the current source.
