# Bug review — Vendor Stock

Review date: 2026-10-02. Target version: Odoo 19.

## VENDORSTOCK-001 — P2: Availability adds supplier stock from other allowed companies

- **Status:** Open.
- **Location:** models/product.py, _compute_vendor_qty_available(); models/sale_order.py, _compute_qty_at_date().
- **Trigger:** A shared product has supplier rows for companies A and B, and a user with both companies allowed opens an order in A.
- **Actual behavior:** The product compute filters only product variant. It sums every visible supplier row without selecting the current/order company. The sale line copies this total and converts its unit, but never restricts suppliers to the order company.
- **Evidence:** Actual AST-extracted product compute with shared supplier rows A=10 and B=70 returned 80. Native seller_ids has no company domain; product_supplierinfo_comp_rule permits rows from all allowed companies (and applicable parents). The addon has no company filter or company context dependency on this quantity.
- **Impact:** Sales availability and vendor-available indicator can count stock belonging to another company's supply arrangements, misleading fulfillment decisions.
- **Suggested fix:** Restrict supplier rows to the relevant company plus deliberately supported shared/parent-company rows, and make company-sensitive computed values context aware. Compute sale-line availability using its order company.
- **Validation needed:** Shared product with distinct supplier stock in two allowed companies, one company allowed, shared supplier rows, parent/child companies and orders from different companies in the same environment.

## Review limitations

All eligible Python, JavaScript and XML source was read. Isolated method execution and native field/rule comparison only; no Odoo database, browser or multi-company integration tests executed. Vendor quantity unit semantics are unspecified, so a supplier-unit conversion defect was not asserted.
