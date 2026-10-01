# Known bugs

Review date: 2026-10-01. Target version: Odoo 19.

## ALTERNATIVE-001 — P2: Alternative-code searches discard product selection domains

- **Status:** Open.
- **Location:** models/product.py, ProductTemplate.name_search() and ProductProduct.name_search().
- **Trigger:** Enable alternative.search_name and search an alternative code in a product selector restricted to sale_ok=True, a product category, or another caller-supplied domain.
- **Actual behavior:** After the superclass search, the overrides replace domain with a search on the alternative name and append linked products without applying the original product domain. Products excluded by the selector can reappear in results.
- **Evidence:** Executed the actual ProductTemplate override with a superclass returning no matches for sale_ok=True and an alternative pointing to a sale_ok=False product. The excluded product was returned; the only alternative search domain was name ilike OEM. The variant override follows the same pattern.
- **Impact:** Sales and purchase selectors can propose products outside their configured eligibility constraints, leading to incorrect selections or later validation failures.
- **Suggested fix:** Preserve the caller domain and intersect alternative-linked product IDs with a product search using that domain before applying limits. Apply the same behavior to templates and variants.
- **Validation needed:** Template and variant searches with sale/purchase flags, category and company filters, duplicate matches, and result limits.

## Review limitations

Findings are based on local source inspection and the isolated reproductions stated above. No database-backed integration tests were run. No fixes have been applied.
