# Confirmed bugs — 2026-10-03

## POSFIX-001 — P2: global discount taxes are mapped a second time

`static/src/app/models/pos_order_line.esm.js:17–30` applies fiscal-position mapping even for `config.discount_product_id`. Native `accounting/pos_order_line_accounting.js:202` explicitly excludes that product: `pos_discount` generates discount lines using the already-mapped `baseLine.tax_ids` (:115–128). With mappings A→B and B→C, a discount belonging to lines taxed B is incorrectly changed to C and its price may be adapted again. Preserve the native discount-product exception.

Evidence: current JS patch executed with native-contract doubles; native base retains B, addon returns C. Fixture `audit_coverage/reproductions/pos_discount_mapping.js`. This isolates mapping, not a full tax-total/receipt simulation. No browser/database workflow executed.

## Other review evidence and limits

Entire Python/JS/manifest source reviewed against native tax helper signatures and POS base-line preparation. Backend native POS also maps tax_ids_after_fiscal_position, so backend remapping is not attributed solely to this addon. Patch also overwrites caller price_unit/tax_ids overrides using stored values; fixture demonstrates lost custom price, but no concrete standard user workflow relying on that override was established, so it is not added as a separate confirmed bug. Global-discount posting consistency still needs database/browser validation.
