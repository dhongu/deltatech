# Confirmed bugs — 2026-10-03

## REORDERLIMIT-001 — P2: minimum search aggregates stock outside the current scope

`models/product_template.py:27–45` reads all internal stock_quant rows with raw SQL, without company, warehouse or location restrictions. The computed field at :59–62 uses native qty_available, which respects those restrictions. A shared product with minimum5, active-company stock0 and other-company stock100 displays below minimum but is excluded by the Below Minimum search. The same mismatch occurs with stock in another warehouse/location. Reuse native stock quantity scope and allowed companies when identifying matching templates.

Evidence: exact `_search_is_below_min()` SQL executed in SQLite with company/location fixtures; search excludes the product in both cases despite local quantity0. Native stock quantity/location domain and template compute traced. Reproduction: `audit_coverage/reproductions/reordering_scope.py`. This confirms classification mismatch; returned product IDs still pass normal product ORM access rules, so direct stock disclosure is not asserted.

## Limits

Full eligible module source reviewed, including the Excel wizard selected-product context guard, calculations and action/view. No Excel artifact was generated; no Odoo/PostgreSQL/domain/UI workflow test executed. Negative search normalization matches current native boolean operators. Historical selected-product context fix is present in source.
