# Changelog

## [18.0.1.2.2] - 2026-07-14

### Fixed
- **Bug**: the supplier's invoice number/date (`invoice_id`/`issue_date` from the source document) were lost whenever the user ran the import wizard without ticking "Create vendor bill" (its default), then created the vendor bill later from the standard purchase order flow. `_process_invoice_data` now auto-creates the vendor bill whenever the source document identifies an invoice number, regardless of the "Create vendor bill" checkbox — the checkbox is still available to force bill creation when the source has no invoice number.
  - Added test `test_vendor_bill_auto_created_when_invoice_id_present`.

## [18.0.1.2.1] - 2026-07-14

### Fixed
- **Bug**: when the purchase order already had lines, source lines whose product wasn't already on the order (e.g. an "Ecovaloare" line added by the supplier that wasn't on the original PO) were silently dropped — no new order line was created and no message was shown. `_process_invoice_data` now adds any unconsumed matched source line as a new purchase order line, mirroring the behavior already used when the order has no lines.
  - Added test `test_new_product_added_as_line_when_order_already_has_lines` reproducing the reported case (order with one existing line, invoice with that line plus an extra unmatched product).

## [18.0.1.2.0] - 2026-07-05

### Changed
- **Refactor**: extracted the format-agnostic matching/bill-creation logic (product matching, supplier price update, purchase order line creation/update, receipt validation, vendor bill creation, log building) into a new shared `purchase.invoice.import.mixin` abstract model (`models/purchase_invoice_import_mixin.py`).
  - `purchase.ubl.import.wizard` now inherits this mixin and keeps only the UBL-XML-specific parts (`_parse_xml`, `_is_ubl_invoice`, `default_get`, `_uom_from_ubl`).
  - No behavior change for UBL import: same model name, fields, and public methods (`_parse_xml`, `_match_product_on_order`, etc.) remain available for other modules that inherit `purchase.ubl.import.wizard` (e.g. `terrabit_mdtrade`).
  - Enables other invoice-import wizards (e.g. a PDF-based importer for a specific vendor) to reuse the same processing via `self._process_invoice_data(invoice_data)`, as long as their parser returns the same intermediate dict shape.

## [18.0.1.1.0] - 2026-05-26

### Added
- **Discount support from e-Factura SPV XML**: Line-level `AllowanceCharge` elements with `ChargeIndicator=false` are now extracted and applied as percentage discounts on purchase order lines.
  - Discount percent is calculated as `allowance_amount / (price * qty) * 100`.
  - Applied on both newly created order lines and existing order lines during update.
  - The gross price (`PriceAmount`) is preserved as `price_unit`; the discount is stored separately in the `discount` field.
- **Test coverage**: Added automated test `test_allowance_charge_discount_applied_on_order_line` verifying correct discount extraction and application (based on real e-Factura SPV invoice data: `PriceAmount=372.20`, `AllowanceCharge/Amount=93.05`, `qty=1` → `discount=25%`).

## [18.0.1.0.0] - 2025-01-01

### Added
- Initial release: import UBL XML vendor invoices to automate purchase order management.
- Automatic product matching by barcode (GS1/EAN), supplier code, internal reference, or name.
- Purchase order line creation and update (quantities and prices) from XML data.
- Supplier price update in vendor pricelist (Supplier Info).
- Stock receipt (picking) validation with quantities from XML.
- Vendor bill creation linked to the purchase order.
- Option to automatically create missing products from UBL data.
- Support for standard UBL Invoice namespaces and common unit code mappings (C62, KGM, LTR, etc.).
