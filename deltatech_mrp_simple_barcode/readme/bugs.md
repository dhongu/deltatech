# Confirmed bugs — 2026-10-03

## MRPBARCODE-001 — P2: ambiguous internal reference causes singleton failure

`models/mrp_simple.py:39–43` searches default_code without limiting/disambiguating results, then `_add_product()` accesses product.id/name (:10–34). Unlike barcodes, internal references are not unique and multiple variants/products can share them. A scan matching more than one internal reference reaches singleton access and fails instead of selecting/asking for a product. Detect multiple matches and provide a selection/error before calling _add_product.

Evidence: exact search/recordset scalar accesses compared with native product fields and ORM singleton contract. Source-only finding; ambiguous-reference scan in browser/ORM unexecuted.

## Limits

All eligible source reviewed, stock simple parent line fields and barcode mixin integration traced. `new()` inverse cache logic links lines when the onchange parent is a NewId, so ignoring the returned child record is not reported as a normal unsaved-form add failure. Saved-parent invocation and duplicate existing lines still require ORM validation. No browser scan tests executed.
