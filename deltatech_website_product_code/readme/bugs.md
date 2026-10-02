# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## WEBCODE-001 — P1: Public search endpoints bypass login-only ecommerce access

- **Status:** Open. Identified on 2026-10-02.
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
