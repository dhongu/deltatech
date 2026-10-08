# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## LABEL-001 — P2: Report wraps an SVG data URI inside another PNG data URI

- **Status:** Fixed in 20.0.1.1.4 — `barcode_image` is a computed Char holding one valid SVG data URI (generated in memory, no `/tmp` file), rendered by the label `<img src>`; the CSS background rule (its selector was also broken by whitespace) is gone. Still open on 19.0.
- **Location:** wizard/product_product_label_print.py, _compute_barcode_image(); views/report_product_labels.xml, set_barcode.
- **Trigger:** Print either supplied PDF label layout for a product with a barcode or internal reference.
- **Actual behavior:** The compute assigns a complete data:image/svg+xml;base64,... URI to barcode_image. The template prepends data:image/png;base64, to that value, yielding a nested URI rather than valid base64 image data (and may render the Binary value as bytes). CSS background-image therefore cannot load the barcode.
- **Evidence:** Complete producer/template expressions inspected. The template does not use the already complete SVG URI directly and does not produce PNG bytes. No PDF rendering executed.
- **Impact:** Printed labels can show text/reference without a usable scannable barcode.
- **Suggested fix:** Keep binary image bytes/base64 and MIME handling consistent; produce one valid URI or use Odoo's image_data_uri utility, without nesting URI prefixes.
- **Validation needed:** Both PDF layouts, valid EAN13 and Code128 internal references, product without a code; verify rendered barcode image and scanning.

## LABEL-002 — P2: Automatically generated lot names are omitted from rebuilt label lines

- **Status:** Open.
- **Location:** wizard/product_product_label_print.py, generate_lots()/get_picking_lines().
- **Trigger:** Enable auto_generate_lots for a lot-tracked incoming move line without an existing lot_id, then print labels.
- **Actual behavior:** Generation assigns a sequence to move_line.lot_name. It then rebuilds label lines through get_picking_lines, which reads lot_id.name only and returns an empty lot string when lot_id is unset. The new lot_name remains on the move line but is not included in label data.
- **Evidence:** Full generation and label rebuild paths inspected. There is no lot creation/assignment between setting lot_name and reading lot_id, and no fallback to lot_name. No database receipt or lot creation executed.
- **Impact:** Layouts using label line lot/get_label_data do not receive the generated lot identifier, defeating printing lot labels before receipt validation.
- **Suggested fix:** Use the pending lot_name when no lot_id exists, or explicitly create/link lots under a validated receipt workflow before rebuilding labels.
- **Validation needed:** New lot_name without lot_id, existing lot_id, multiple incoming lots and print-before-validation; label data must contain the actual generated identifier.

## Review limitations

All eligible Python/XML module source manually reviewed: selected products/templates/sales/pickings/lots/quants, warehouse defaults and lot-only option, lot generation, prices, barcode image/file handling, URL generation, report layouts/actions and ACLs. Source-confirmed findings only; no Odoo wizard, PDF rendering, barcode filesystem writes or integration tests executed.
