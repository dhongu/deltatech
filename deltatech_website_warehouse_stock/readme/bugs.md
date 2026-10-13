# Confirmed bugs — integrated review 2026-10-03

## WEBWAREHOUSE-001 — P1: public page exposes warehouses outside the website company

- **Status:** Fixed in 19.0.0.0.3. `get_warehouse_stock_distribution()` (run with `sudo()` from the
  product page) now restricts the warehouse search explicitly to the current website's company, so
  warehouse names and quantities of other companies are no longer exposed. Regression tests added.

`views/website_sale_stock_templates.xml:16` calls the distribution method with `product.sudo()`. `models/product.py:13` searches all warehouses marked for display, with no website/company filter; the field defaults true for every warehouse. A public company-A site thus includes company-B warehouse names in its distribution. For shared products and a location context without a restricting warehouse context, native quantity computation can also disclose B stock: explicit locations determine the quant domain and sudo bypasses company rules. Scope the warehouse search to the website company and its explicitly intended public warehouses.

Evidence: exact method with isolated warehouse fixture includes a foreign warehouse and its supplied quantity; native location/quantity domains and QWeb sudo inspected. Fixture proves custom flow, not actual database company isolation. Reproduction: `audit_coverage/reproductions/pos_warehouse_notifications.py`. The definite source disclosure is the foreign warehouse name; quantity visibility also depends on product/context. No public-browser/database scenario executed.

## Review limits

Entire module source reviewed with native template quantities and website stock API. Template-level variant aggregation is explicitly documented and excluded as an intentional behavior. Threshold boundary follows documented <= threshold numeric output. Site-specific configuration and actual public requests remain unexecuted.
