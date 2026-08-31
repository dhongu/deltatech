# Changelog

## [19.0.1.4.0] - 2026-08-31

### Added
- **Warning indicator on the import wizard** (`has_warning`, ticket #9287): set alongside
  `log`/`log_html` so a headless caller can tell whether a run needs a human's attention without
  re-parsing the log text. Deliberately narrower than "any warning-classified message": only a
  **total that doesn't add up** and **lines the matcher couldn't place** count. Routine steps of an
  unattended import — bill creation skipped because the order isn't confirmed yet, no receipt to
  validate — also classify as "warning" via `_classify_message`'s generic keywords and would
  otherwise fire on every successful headless import.
- **Review activity on the purchase order** (ticket #9287): when the headless import sets
  `has_warning`, `_process_attachments_for_post` schedules a `mail.mail_activity_data_todo`
  activity "SPV import needs review" on the order, assigned to the order's buyer (`user_id`,
  falling back to the current user), with the import log as the activity note. A plain chatter note
  was not enough: on a production database a total mismatch and 4 unmatched lines sat unnoticed in
  the chatter for hours, buried among the SPV cron's other automated traffic. The activity is
  guarded on its summary, because the SPV cron is known to reprocess the same message (observed
  ~10x in one morning) and would otherwise pile up duplicates.
- Tests `test_unmatched_line_schedules_activity_instead_of_silent_chatter_note` (including the
  reprocessing case) and `test_matched_import_does_not_schedule_activity`.
- **Screenshot test** `tests/test_screenshots.py` (tag `fise_screenshots`): generates the consultant
  sheet's captures for the mapping preview (all three match colors) and for the review activity.

### Changed
- The headless import now posts the **color-coded** log (`log_html`) on the purchase order instead
  of the plain-text `log`, so mismatches and unmatched lines stand out in red/orange instead of
  blending into a wall of text.
- **Shorter log.** Updated prices are no longer listed line by line — a single
  "Identified products and updated prices for %s line(s)." message replaces the per-line dump.
  Created products keep their per-product detail but gain a count in the header
  ("Created products (%s):"). On a real SPV import the log was long enough that the warning at the
  end was below the fold.
- Log messages now say "source document" instead of "XML", because the same mixin serves the PDF
  import wizards (Marso, Delta, Sigemo, Procar), not just UBL XML.

### Fixed
- **Romanian translations were not applied at all** for terms added since the last `.pot`
  regeneration (the whole preview wizard: `Supplier Code`, `Match Type`, `By name`, `Not found`,
  the legend banner, and the `SPV import needs review` activity title). `PoFileReader` merges
  `i18n/ro.po` with `i18n/<module>.pot` to refresh references, and `polib.merge()` marks every
  `.po` entry absent from the `.pot` as **obsolete** — which the reader then skips silently. The
  `.pot` was older than `ro.po`, so exactly the new terms were dropped while the old ones kept
  working. Regenerated the `.pot` and resynchronized `ro.po` (the regeneration merges the info
  icon with its `<span>` into a single term, so the banner needed a new entry).

## [19.0.1.3.0] - 2026-08-24

### Added
- **Mapping preview in the import wizard** (ticket #9315): the interactive flow is now
  two-step — "Preview" parses the XML and shows one line per invoice line with the product
  the matcher found and how it found it, color-coded: green = matched by supplier code or
  barcode (trustworthy), yellow = matched only by name (double-check), red = no match (a new
  product would be created). The user can pick a different product on any line before
  confirming the import; manual choices override automatic matching
  (`_process_invoice_data(product_map=...)`). The headless entry point `action_import` is
  unchanged, so automated callers keep working.

### Fixed
- **Bug** (ticket #9315): `_process_attachments_for_post` always ran the headless UBL import
  with `create_missing_products=True`. This is fine for the interactive wizard, where a user
  reviews what gets created, but it's also the only entry point for XML attachments posted by
  automated callers (e.g. `l10n_ro_message_spv_purchase`, since ticket #9287 started attaching
  the SPV XML on purchase orders created before the vendor bill exists). When the source invoice
  line has no supplier product code and its name doesn't match an existing product exactly, the
  headless import silently created a duplicate product with no one reviewing it.
  `_process_attachments_for_post` now honors a `purchase_ubl_no_new_products` context key: when
  set, the headless import runs with `create_missing_products=False` and leaves unmatched lines
  in the wizard's "unmatched products" log instead of creating a product.

## [19.0.1.2.4] - 2026-08-20

### Fixed
- **Bug**: `depends` listed `purchase` + `stock` separately, but the module actually uses fields
  defined by their glue module `purchase_stock` (`purchase.order.picking_ids`,
  `stock.picking.purchase_id`) in `_find_receipt`/`_validate_receipt_quantities`.
  `purchase_stock` is `auto_install=True`, and CI's test database init runs with
  `--skip-auto-install` (Odoo ≥ 19) - so it was only ever getting installed incidentally, when
  another module in the same CI shard happened to declare it explicitly. `depends` now lists
  `purchase_stock` directly instead of `purchase` + `stock`.

## [19.0.1.2.3] - 2026-08-20

### Fixed
- **Bug** (found via ticket #9287): auto-creating the vendor bill whenever the source document
  identifies an invoice number (added in 19.0.1.2.1) ran regardless of the purchase order's
  state. A draft/unconfirmed order has `qty_to_invoice = 0` on every line
  (`purchase_order_line._compute_qty_invoiced` only computes a nonzero value once the order is
  `state == "purchase"`), so `action_create_invoice()` still "succeeded" but produced a vendor
  bill with every line at zero quantity/amount — a useless ghost document. This hit the SPV
  auto-import flow, where a purchase order can be created and attached to its XML before it is
  ever confirmed.
  - `_process_invoice_data` now skips vendor bill creation (logging why) when the resolved
    order isn't confirmed yet (`state not in ("purchase", "done")`), instead of silently
    creating an empty bill.
  - Added test `test_vendor_bill_skipped_when_order_not_confirmed`.

## [19.0.1.2.2] - 2026-07-18

### Fixed
- **Bug** (ported from 18.0 PR #2649): purchase order lines for service products with `purchase_method="receive"` (e.g. Marso's "Ecovaloare" eco-tax lines) never get a `qty_received` from stock moves, since services have no stock picking. Only `_validate_receipt_quantities` (used for physical products) previously set received quantities, so these service lines stayed at `qty_to_invoice == 0` and `action_create_invoice()` silently dropped them from the vendor bill even though they were present on the order.
  - `_process_invoice_data` now marks a line as received (`qty_received_manual` = ordered quantity) whenever its `qty_received_method` is `"manual"`, for both updated existing lines and newly added ones.
  - Added test `test_service_line_receive_policy_is_marked_received_for_billing`.

## [19.0.1.2.1] - 2026-07-14

### Fixed
- **Bug** (ported from 18.0 PR #2645): when the purchase order already had lines, source lines whose product wasn't already on the order (e.g. an "Ecovaloare" line added by the supplier that wasn't on the original PO) were silently dropped — no new order line was created and no message was shown. `_process_invoice_data` now adds any unconsumed matched source line as a new purchase order line, mirroring the behavior already used when the order has no lines.
  - Added test `test_new_product_added_as_line_when_order_already_has_lines`.
- **Bug** (ported from 18.0 PR #2645): the supplier's invoice number/date (`invoice_id`/`issue_date` from the source document) were lost whenever the user ran the import wizard without ticking "Create vendor bill" (its default), then created the vendor bill later from the standard purchase order flow. `_process_invoice_data` now auto-creates the vendor bill whenever the source document identifies an invoice number, regardless of the "Create vendor bill" checkbox.
  - Added test `test_vendor_bill_auto_created_when_invoice_id_present`.

## [19.0.1.2.0] - 2026-07-05

### Changed
- **Refactor** (ported from 18.0): extracted the format-agnostic matching/bill-creation logic (product matching, supplier price update, purchase order line creation/update, receipt validation, vendor bill creation, log building) into a new shared `purchase.invoice.import.mixin` abstract model (`models/purchase_invoice_import_mixin.py`).
  - `purchase.ubl.import.wizard` now inherits this mixin and keeps only the UBL-XML-specific parts (`_parse_xml`, `_is_ubl_invoice`, `default_get`, `_uom_from_ubl`).
  - No behavior change for UBL import: same model name, fields, and public methods remain available.
  - Enables other invoice-import wizards (PDF-based importers for Marso, Delta, Sigemo, Procar) to reuse the same processing via `self._process_invoice_data(invoice_data)`.
  - Preserves the 19.0-specific API adaptations already present in this branch (`product_uom_id` instead of `product_uom` on purchase order lines, `move_ids` instead of the removed `move_ids_without_package`, `_set_quantity_done`/`picked` instead of `qty_done`).

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
