# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## WEBCODE-001 — P1: Public search endpoints bypass login-only ecommerce access

- **Status:** Fixed in 19.0.1.3.5 — `_search_products_by_code()` returns no product when `website.has_ecommerce_access()` is false, so `/shop/products-json` and `/shop/products-search` give an empty list to visitors of a shop restricted to logged-in users; `/shop/product-code/<code>` redirects them to the login page before searching, as `/shop/<product>` does. Covered by tests in `tests/test_ecommerce_access.py` (public shop, login-only shop as visitor and as logged-in user, product-code link).
- **Location:** `controllers/website_sale.py:30–109, products_json_by_code(), products_search_by_code(), _search_products_by_code()`.
- **Trigger:** Set the website ecommerce_access to logged_in, leave published saleable products, and anonymously call /shop/products-json or /shop/products-search.
- **Actual behavior / impact:** The shared search helper never calls website.has_ecommerce_access(). It searches with sudo and returns product names, SKUs and prices even when the normal shop and product pages require login. sale_product_domain() filters products and websites but does not enforce the login-only gate.
- **Evidence:** Executed the extracted helper with a public user and website.has_ecommerce_access() returning False: a published product and price 100 were returned. Compared local website_sale controllers and website._search_get_details(), which apply the gate.
- **Suggested fix:** Check ecommerce access before searching or returning product information on both endpoints, following the standard website policy.
- **Validation needed:** HTTP-test anonymous and authenticated calls on login-only and public websites; verify the JSON and HTTP endpoints both honor the setting.
- **Limitations:** Extracted-method checks use mocked records; database-backed Odoo integration tests were not run in this pass.

## WEBCODE-002 — P2: Product-code links cannot resolve multi-variant SKUs

- **Status:** Open. Identified on 2026-10-02.
- **Location:** `controllers/website_sale.py:24–28, product_by_code()`.
- **Trigger:** Create a template with two variants whose SKUs are RED and BLUE, then open /shop/product-code/RED.
- **Actual behavior / impact:** The route searches product.template.default_code only. Core Odoo computes this field from the variant only for a single-variant template, and sets it to False for multiple variants. A valid variant SKU therefore returns 404.
- **Evidence:** Verified core product.template._compute_default_code() and _compute_template_field_from_variant_field(); executed the extracted route and confirmed the only search domain is template default_code = the supplied SKU. The same module search helper already uses product_variant_ids.default_code.
- **Suggested fix:** Resolve the code on variants or the variant relation, and open the corresponding template with that variant selected while preserving website visibility checks.
- **Validation needed:** HTTP-test both codes of a two-variant template and a single-variant template; verify correct variant selection and rejection of inaccessible products.
- **Limitations:** Extracted-method checks use mocked records; database-backed Odoo integration tests were not run in this pass.

## WEBCODE-003 — P2: Multi-code search silently clips the candidate set before counting and ranking

- **Status:** Open.
- **Location:** models/product_template.py, _search_fetch_multi_code().
- **Trigger:** A pasted code list matches more than max(limit*20,500) products in one search field.
- **Actual behavior:** Each field search is limited and sorted by id, then only those truncated IDs are considered by the final website ordering/search_count. Matching products beyond the intermediate limit are absent even when they should rank first; count and pagination reflect only the clipped set.
- **Evidence:** Executed the actual AST-extracted method with a mock search model containing 501 matches and limit 20: count is 500, and the highest website-ranked product (ID 501) never reaches the final candidates. No PostgreSQL/website query executed.
- **Impact:** Customers cannot reach some matching products through pagination, and prominent products can be omitted from the first page. Counts vary with intermediate limits rather than actual matches.
- **Suggested fix:** Combine complete matching domains/IDs in a database-level query, preserving indexed branches without a silent candidate cap; apply the page limit only after full ordering and count the full union.
- **Validation needed:** More than 500 matches per branch, overlapping branches, reverse website order versus IDs and successive pages; results/count must agree with the complete matching set.

## WEBCODE-004 — P2: Legacy nonnumeric minimum-search configuration crashes ordinary searches

- **Status:** Open.
- **Location:** models/product_template.py, _search_build_domain(); models/res_config_settings.py, get_values().
- **Trigger:** website_search.min_term_length contains a legacy False string or another nonnumeric value and a nonempty search uses the regular fallback.
- **Actual behavior:** The search hook calls int(get_param(...)) without exception handling. The settings reader explicitly treats legacy nonnumeric values as disabled (zero), but runtime search does not follow that policy, unlike the other two numeric search helpers.
- **Evidence:** Executed the actual AST-extracted hook with get_param returning False as text: ValueError, invalid literal for int() with base 10. Compared the settings get_values and the guarded standalone/multi-code helpers. Mock environment only.
- **Impact:** Shop searches can fail until an administrator resaves settings or repairs the parameter, despite the settings page displaying a safe disabled value.
- **Suggested fix:** Use one shared robust parser/default policy for all runtime and settings reads; normalize legacy values in migration if needed.
- **Validation needed:** Unset, zero, positive integer, legacy False, empty and invalid text values; regular/exact/pasted searches must remain usable.

## Full source review — 2026-10-02

All eligible Python/XML files, including migrations, were manually read. Earlier findings remain open in the inspected source. New reproductions use AST-extracted methods with mock search/invoice objects; no browser, PostgreSQL search, migration or Odoo integration tests executed.
