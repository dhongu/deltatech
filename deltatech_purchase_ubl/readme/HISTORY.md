## 19.0.1.4.21 (2026-10-24)

- Matching by name without spaces (the last matching step, UBL-010, #3760): the name
  is read in the user's language with English as fallback, so on a Romanian database a
  product created in English is found too; case is ignored; archived products and
  products of other companies are left out; and the name must be unique, as in the
  step before it, instead of taking one of several products at random.

## 19.0.1.4.20 (2026-10-22)

- Listed on Odoo Apps as *Purchase UBL Import* (was *Purchase UBL*). The technical name `deltatech_purchase_ubl` does not change.

## 19.0.1.4.19 (2026-10-21)

- The button of the purchase order and the title of the wizard are now *Import Invoice*
  (*Import factură* in Romanian) instead of *Import UBL*: the wizard also takes the
  vendor invoice PDF (with *Purchase PDF AI Import*), not only the UBL XML.

## 19.0.1.4.18 (2026-10-20)

- The order is compared with the document on the value without VAT and, when the
  document states it, on the total with VAT, and the log shows both. Before, only the
  total with VAT was checked when the document had one, or else only the value without
  VAT. An intra-community invoice at 0% imported on an order whose lines took the
  domestic 21% matched without VAT and passed unnoticed. Any difference also keeps the
  import from going straight through and opens the preview.
- A line whose VAT differs from the rate on the document is reported in the log
  (only reported: the order's VAT comes from the products and the vendor's fiscal
  position, which is where it is corrected). A reverse charge or intra-community tax
  counts as 0% against an intra-community (K) or reverse charge (AE) document, but is
  reported against an exempt, zero-rated, out-of-scope or export document (E, Z, O, G),
  where the buyer does not self-assess the VAT. A 0% rate counts only with one of these
  categories, or when the reader of the document vouches for its rates
  (`tax_percent_read`).

## 19.0.1.4.17 (2026-10-20)

- The description column of the import preview is now labelled "Vendor Description"
  instead of "Description (XML)": the lines can also come from a PDF invoice.
- An order created by the Upload button of the purchase list (an empty draft whose
  vendor is the current user or the company) takes its vendor from the document
  when it is imported. Before, the lines were imported, and vendor prices saved,
  under the user, with only a warning that the VAT number differs. An unknown
  vendor stops the import with the usual message.

## 19.0.1.4.16 (2026-10-20)

- New extension point `_parse_source`: every step of the import wizard reads the
  uploaded file through it (UBL XML here), so an extension can import other
  formats with the same preview, matching and vendor bill creation. Used by
  *Purchase PDF AI Import*.

## 19.0.1.4.15 (2026-10-20)

- Fixed: in Romanian (and any language other than English), every message of the
  import log was shown in blue as information. The level was guessed from English
  words in the text, which the translation removes; it is now set where each
  message is created. Each message also starts with a colored emoji (✅ ⚠️ ❌ ℹ️),
  also in the plain-text log and in the note of the review activity.
- Fixed: the import window was titled "purchase.ubl.import.wizard,1" when opened
  as a page and "Odoo" when opened as a dialog. It is now titled "Import UBL",
  with the file name.
- Fixed: after a clean invoice was imported directly from an SPV message, the
  web client showed an error dialog instead of opening the purchase order. The
  action opened after the "Invoice imported" notification had no `views`.
- Romanian translation of the texts added in 19.0.1.4.13 and 19.0.1.4.14: the
  line actions of the import preview, the preview banner, the "Open Purchase
  Order" button, the "Invoice imported" notification, the deferred vendor bill
  message and the unit of measure warnings. The `.pot` template is regenerated.
- Screenshots for the consultant sheet: the import preview with the action
  column and the import options, and the result step with the "Open Purchase
  Order" button.

## 19.0.1.4.14 (2026-10-20)

- Changed: in the import preview, each line now has an action: *Use product*,
  *Create new product* or *Ignore*. A line without a product is ignored by
  default; a new product is created only when the user chooses *Create new
  product* on that line. The global "Create missing products" option is no
  longer shown in the wizard (it still applies to the automatic import).
- The preview also shows the *Update vendor prices*, *Create vendor bill* and
  *Validate receipt* options, and the result step has an *Open Purchase Order*
  button.
- New *preview or import* entry point (`action_preview_or_import`): when every
  line is matched by vendor code or barcode and, after the import, the order
  total equals the invoice total, the invoice is imported straight away and the
  user only gets a notification (the import log is posted on the order).
  Otherwise the import is rolled back and the preview opens.
- New context key `purchase_ubl_skip_auto_import`: a caller that opens the
  import wizard itself attaches the XML to the order without the automatic
  import.

## 19.0.1.4.13 (2026-10-19)

- Changed: the automatic import of an XML attached to a purchase order no longer
  creates the vendor bill when a line of the invoice could not be matched to a
  product. That bill missed the unmatched lines, and resolving them later on the
  order did not update it. The import log says why the bill was skipped; create
  it once every line is resolved.
- Fixed: an invoice line without a vendor code erased the code already saved on
  the vendor price row of the product.
- New extension point for the lines the automatic import could not match, used by
  *Purchase UBL AI Product Matching*.

## 19.0.1.4.12 (2026-10-16)

- Fixed: the check for an existing vendor bill with the same supplier invoice
  number looked at every company the user had access to. It now looks only in
  the company of the purchase order.
- Fixed: updating the vendor price of a product variant could overwrite the
  vendor price row of another variant of the same product, or a row of another
  company. Only the row of the imported variant in the order's company (or a
  row shared between companies) is updated now; a new row is created otherwise.
- Fixed: the unit code SET was mapped to a unit that does not exist in Odoo 19
  and was handled as Units. A unit named "Set" is used when one is defined. A
  unit code that is not recognised is now reported in the import log.

## 19.0.1.4.11 (2026-10-12)

- Fixed: the vendor was not found by its tax id when the invoice and the partner
  wrote the Romanian CUI differently (with or without the RO prefix, with
  spaces); only an exact name match was left. The tax ids are now compared
  without spaces and without the RO prefix (other countries keep theirs), which
  also removes the false "Supplier VAT ... differs" warning. For a supplier not
  registered for VAT, the CUI is read from PartyLegalEntity/CompanyID.

## 19.0.1.4.10 (2026-10-12)

- Fixed: a supplier credit note (a CreditNote document, or an Invoice with type
  code 381) was imported as an invoice. A CreditNote created a vendor bill from
  the order instead of a refund; an Invoice 381 wrote negative quantities on the
  order lines and overwrote the vendor prices. Credit notes are now recognised
  and not imported: the order is left as it is, the log shows a warning and the
  automatic import schedules the "SPV import needs review" activity. Record the
  vendor refund manually.

## 19.0.1.4.9 (2026-10-12)

- Fixed: a supplier invoice imported on a purchase order with nothing left to
  invoice (already fully invoiced, or billed on received quantities with nothing
  received yet) created a vendor bill with every line at zero quantity. The bill
  is now skipped with a message in the log, and the automatic import schedules
  the "SPV import needs review" activity on the order, since it may be a
  duplicate invoice or an extra charge.

## 19.0.1.4.8 (2026-10-12)

- Fixed: a receipt validated without a purchase order context (or still waiting
  for another operation) stayed undone when the invoice covered only part of it,
  while the log said "Receipt updated". The received quantities are now validated
  and the rest goes to a backorder. When the receipt still cannot be validated,
  the log shows a warning instead.

## 19.0.1.4.7 (2026-10-12)

- Tests: 33 new tests for the automatic import on attachment, XML parsing and
  detection, wizard defaults and preview, vendor/order resolution, product
  matching, units of measure, partial receipts and vendor bill taxes. Local
  coverage of the module goes from 82.5% to 95.8%. No change in behaviour.

## 19.0.1.4.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.4.5 (2026-10-08)

- Fixed UBL-001: a line with an explicit 0% VAT kept the default 21% tax of the
  order on the vendor bill. The 0% rate is now applied when the line declares a
  zero-rated (Z), exempt (E), out-of-scope (O, e.g. a supplier not registered
  for VAT) or export (G) category. For reverse charge (AE), intra-community (K)
  or lines without a category the taxes of the order are kept, as before; the
  PDF imports, which report 0 when they cannot read the rate, are not affected.
- Fixed UBL-002: two lines of the same product with different VAT rates both
  received the last rate. Each bill line now takes the rate of the source line
  matched to its purchase order line.
- Fixed UBL-003: with receipt validation, a product present on several source
  lines (e.g. 2 + 3 units) was received with the last quantity on every stock
  move (3 + 3). The quantities are now summed per product and split over the
  moves, so the received total matches the document (5).
- A bill line whose taxes already match the source rate is left unchanged, and
  the tax is searched in the bill company instead of the current company.

## 19.0.1.4.4 (2026-10-03)

- Fixed: the import copied the source quantity and unit price into purchase lines, receipts and
  vendor prices without looking at the source unit (`unitCode`). A kg order line receiving
  "1000 GRM at 0.01" became 1000 kg at 0.01. Quantities and prices are now converted from the
  source unit to the unit of the existing order line, of the stock move and of the existing
  vendor pricelist row; new order lines and new vendor prices keep the source unit when it is
  compatible with the product unit. A source unit that is unknown is treated as before (same unit
  as the destination); an incompatible unit is left unconverted and reported as a warning in the
  import log. The `MLT`/`MMT` codes now resolve to millilitre/millimetre (they fell back to Units)
  and `DZN` resolves to Dozens (UBL-005). Imported quantities, prices and receipt quantities change
  for documents whose unit differs from the order/product unit.

# 19.0.1.4.3

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.1.4.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## [19.0.1.4.1] - 2026-09-02

### Fixed

- **Version bump so a build can be told apart by its translations.** The RO translation fix of
  19.0.1.4.0 (regenerated `.pot`, resynced `ro.po`) landed *without* touching `__manifest__.py`,
  so code from before and after it both report `19.0.1.4.0`. On a customer database
  `ir.module.module.latest_version` therefore proved nothing about whether the translations were
  actually on disk — a Romchim check had to fall back to reading `code_translations` in a shell.
  Python code translations are read from `i18n/*.po` on disk at runtime (`CodeTranslations`), not
  from the database, so no `-u` can compensate for a stale build: the manifest version is the only
  handle an audit has. Bumped so it is one.

## [19.0.1.4.0] - 2026-08-31

### Added

- **Warning indicator on the import wizard** (`has_warning`): set alongside
  `log`/`log_html` so a headless caller can tell whether a run needs a human's attention without
  re-parsing the log text. Deliberately narrower than "any warning-classified message": only a
  **total that doesn't add up** and **lines the matcher couldn't place** count. Routine steps of an
  unattended import — bill creation skipped because the order isn't confirmed yet, no receipt to
  validate — also classify as "warning" via `_classify_message`'s generic keywords and would
  otherwise fire on every successful headless import.
- **Review activity on the purchase order**: when the headless import sets
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
  import wizards (supplier-specific importers), not just UBL XML.

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

- **Mapping preview in the import wizard**: the interactive flow is now
  two-step — "Preview" parses the XML and shows one line per invoice line with the product
  the matcher found and how it found it, color-coded: green = matched by supplier code or
  barcode (trustworthy), yellow = matched only by name (double-check), red = no match (a new
  product would be created). The user can pick a different product on any line before
  confirming the import; manual choices override automatic matching
  (`_process_invoice_data(product_map=...)`). The headless entry point `action_import` is
  unchanged, so automated callers keep working.

### Fixed

- **Bug**: `_process_attachments_for_post` always ran the headless UBL import
  with `create_missing_products=True`. This is fine for the interactive wizard, where a user
  reviews what gets created, but it's also the only entry point for XML attachments posted by
  automated callers (e.g. `l10n_ro_message_spv_purchase`, since the SPV import started attaching
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

- **Bug**: auto-creating the vendor bill whenever the source document
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

- **Bug** (ported from 18.0): purchase order lines for service products with `purchase_method="receive"` (e.g. "Ecovaloare" eco-tax lines) never get a `qty_received` from stock moves, since services have no stock picking. Only `_validate_receipt_quantities` (used for physical products) previously set received quantities, so these service lines stayed at `qty_to_invoice == 0` and `action_create_invoice()` silently dropped them from the vendor bill even though they were present on the order.
  - `_process_invoice_data` now marks a line as received (`qty_received_manual` = ordered quantity) whenever its `qty_received_method` is `"manual"`, for both updated existing lines and newly added ones.
  - Added test `test_service_line_receive_policy_is_marked_received_for_billing`.

## [19.0.1.2.1] - 2026-07-14

### Fixed

- **Bug** (ported from 18.0): when the purchase order already had lines, source lines whose product wasn't already on the order (e.g. an "Ecovaloare" line added by the supplier that wasn't on the original PO) were silently dropped — no new order line was created and no message was shown. `_process_invoice_data` now adds any unconsumed matched source line as a new purchase order line, mirroring the behavior already used when the order has no lines.
  - Added test `test_new_product_added_as_line_when_order_already_has_lines`.
- **Bug** (ported from 18.0): the supplier's invoice number/date (`invoice_id`/`issue_date` from the source document) were lost whenever the user ran the import wizard without ticking "Create vendor bill" (its default), then created the vendor bill later from the standard purchase order flow. `_process_invoice_data` now auto-creates the vendor bill whenever the source document identifies an invoice number, regardless of the "Create vendor bill" checkbox.
  - Added test `test_vendor_bill_auto_created_when_invoice_id_present`.

## [19.0.1.2.0] - 2026-07-05

### Changed

- **Refactor** (ported from 18.0): extracted the format-agnostic matching/bill-creation logic (product matching, supplier price update, purchase order line creation/update, receipt validation, vendor bill creation, log building) into a new shared `purchase.invoice.import.mixin` abstract model (`models/purchase_invoice_import_mixin.py`).
  - `purchase.ubl.import.wizard` now inherits this mixin and keeps only the UBL-XML-specific parts (`_parse_xml`, `_is_ubl_invoice`, `default_get`, `_uom_from_ubl`).
  - No behavior change for UBL import: same model name, fields, and public methods remain available.
  - Enables other invoice-import wizards (PDF-based supplier importers) to reuse the same processing via `self._process_invoice_data(invoice_data)`.
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
