# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## ALTERNATIVE-001 — P2: Alternative-code searches discard product selection domains

- **Status:** Fixed in 19.0.2.1.5. The template and variant overrides now share one helper that adds the alternative code as a condition (`alternative_ids.name` / `product_tmpl_id.alternative_ids.name`) of a `search_fetch` on the product model itself, combined with the caller's domain, excluding the IDs already found and limited to the remaining slots. The caller's domain and the product record rules (company) therefore apply. Also fixed: variants are returned with `display_name` instead of `name`; `limit=None` no longer raises `TypeError`; negative operators no longer add alternative matches. Covered by `tests/test_name_search.py` (sale_ok, category, company, limit, `limit=None`, display name).
- **Location:** models/product.py, ProductTemplate.name_search() and ProductProduct.name_search().
- **Trigger:** Enable alternative.search_name and search an alternative code in a product selector restricted to sale_ok=True, a product category, or another caller-supplied domain.
- **Actual behavior:** After the superclass search, the overrides replace domain with a search on the alternative name and append linked products without applying the original product domain. Products excluded by the selector can reappear in results.
- **Evidence:** Executed the actual ProductTemplate override with a superclass returning no matches for sale_ok=True and an alternative pointing to a sale_ok=False product. The excluded product was returned; the only alternative search domain was name ilike OEM. The variant override follows the same pattern.
- **Impact:** Sales and purchase selectors can propose products outside their configured eligibility constraints, leading to incorrect selections or later validation failures.
- **Suggested fix:** Preserve the caller domain and intersect alternative-linked product IDs with a product search using that domain before applying limits. Apply the same behavior to templates and variants.
- **Validation needed:** Template and variant searches with sale/purchase flags, category and company filters, duplicate matches, and result limits.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. ALTERNATIVE-001 was fixed afterwards (see its status); the fix is covered by database-backed tests.

## Reverification — 2026-10-01

Compared the current local `19.0` source with the original audit snapshot. Repository HEAD: `7e93258ed`. This pass verifies source changes; module integration tests and upgrade migrations were not executed on an Odoo database.

- **ALTERNATIVE-001 — fixed in source:** the changed implementation addresses the originally documented failure. See the fix description and regression tests above. Deployment and database upgrade are outside this verification.

Full eligible source review — 2026-10-02: ALTERNATIVE-001 remains fixed in source. ALTERNATIVE-002 adds a dependency-cache finding; no database tests rerun.

## ALTERNATIVE-002 — P2: Alternative-code cache is not invalidated when child names or hide flags change

- **Status:** Open.
- **Location:** models/product.py, ProductTemplate._compute_alternative_code().
- **Trigger:** Read a product alternative_code, then rename or hide an existing product.alternative record in the same environment and read the code again.
- **Actual behavior:** The compute reads child name and hide but declares only @api.depends("alternative_ids"). Updates to an existing child name/hide do not change relation membership and are absent from the recomputation dependency paths. Related sale/purchase/stock display fields can retain the old concatenated value.
- **Evidence:** Complete models/views/cron source inspected. Decorator contains only alternative_ids, while the body reads cod.name and cod.hide; there is no custom write/cache invalidation hook. Compared local ORM fields.resolve_depends, which traverses declared dotted paths. Source evidence only; no database cache regression executed.
- **Impact:** A changed or hidden code can remain displayed until the environment/cache is refreshed, including after the split-multi-code method renames existing records.
- **Suggested fix:** Declare alternative_ids.name and alternative_ids.hide dependencies in addition to membership and verify delegated/related displays refresh.
- **Validation needed:** Pre-read cache, rename/hide/unhide/create/unlink codes and split a multi-code record; template, variant and order/stock related code fields must update in the same transaction.
