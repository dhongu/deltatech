# Bug review — eCommerce Stock Availability

Review date: 2026-10-02. Target version: Odoo 19.

## WEBSTOCK-001 — P2: Vendor availability uses the first unfiltered template supplier

- **Status:** Open.
- **Location:** models/product.py, _get_combination_info().
- **Trigger:** A variant shares its template with other variants having supplier-specific rows, or the first supplier belongs to another company, is inactive or has expired terms.
- **Actual behavior:** The sudo product's seller_ids[0] supplies qty_available and delay without filtering product_id, company_id, active supplier or date_end. Only a future date_start adjusts the displayed delay. Template seller_ids includes rows for other variants.
- **Evidence:** Complete source inspected against core product.product._prepare_sellers/_get_filtered_sellers and product.supplierinfo._get_filtered_supplier, which explicitly filter these conditions. Executed the actual method extracted by AST with variant 2 and first seller for variant 1/company 99 expired in 2020: it reports availability_vendor=100 and purchase_lead_time=2, although the applicable seller has zero stock and delay 7. Mock records only; no website request executed.
- **Impact:** Product pages can claim vendor stock and fast delivery that are unavailable for the selected variant/company. Sudo allows otherwise inaccessible company-specific supplier information to influence the public message.
- **Suggested fix:** Resolve eligible suppliers for the selected variant and website company, with an explicit validity/quantity policy; use the same selected supplier for stock and lead time.
- **Validation needed:** Variant-specific suppliers, shared suppliers, multiple companies, inactive vendors, expired/future offers and minimum quantities; the message must reflect the eligible supplier.

## WEBSTOCK-002 — P2: Cart delivery badges ignore the website warehouse and line unit

- **Status:** Open.
- **Location:** views/website_sale_stock_templates.xml, active cart_line_description_following_lines template.
- **Trigger:** Website warehouse has no available stock but another warehouse has stock, or the website sells a product in an alternative unit such as dozen.
- **Actual behavior:** The cart badge compares line.product_id.free_qty directly with line.product_uom_qty. It neither restricts free_qty to the order/website warehouse nor converts the product default unit to line.product_uom_id. The partial badge also prints an unconverted quantity.
- **Evidence:** Entire active QWeb extension read. Local website_sale_stock website._get_product_available_qty and sale.order._get_product_available_qty explicitly apply warehouse_id; native combination info additionally converts to the selected unit. This template calls none of those helpers. With six free units and a cart line of one dozen, the direct comparison 6 >= 1 chooses Immediate delivery although only half the requested quantity is available. Source/arithmetic evidence only; no QWeb/browser integration execution.
- **Impact:** The cart can promise immediate delivery when the selling warehouse cannot fulfill the order or when the available physical quantity is insufficient.
- **Suggested fix:** Use order/website-scoped available quantity converted into the line unit for both the full/partial decision and displayed quantity.
- **Validation needed:** Two warehouses with stock only outside the website warehouse, Unit/Dozen lines and partial availability; badges must agree with the product page and fulfillment quantities.

## Review limitations

All eligible Python, JavaScript and XML source was read, including inactive templates and the unimported controller. The supplier reproduction used mocked records. No browser tour, database test, live stock query or template rendering was executed.
