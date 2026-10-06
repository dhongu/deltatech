# Bug review — deltatech_kit_price

Review date: 2026-10-02. Target version: Odoo 19.

## KITPRICE-001 — P2: Kit cost fallback can select another product variant bill

- **Status:** Open.
- **Location:** models/sale_order_line.py, get_available_phantom_bom_id().
- **Trigger:** A product variant has no variant-specific phantom bill while another variant of the same template has one.
- **Actual behavior / impact:** The fallback filters only phantom type and product template, without requiring product_id=False. It can select a bill dedicated to a different variant and use its component cost on the current sale line.
- **Evidence:** Actual extracted selector with a bill for variant 2 and a requesting variant 1 selected that bill. Native _bom_find_domain restricts selection to the current variants or product_id=False template bills.
- **Suggested fix:** Use native company-aware _bom_find or explicitly restrict template fallback to variant-free bills.
- **Validation needed:** Two variants with distinct costs, template-only bills, variant-specific precedence and multiple allowed companies.

## Review limitations

All eligible source read. Native methods compared; kit selection executed only with mocked records. No Odoo access, invoice or sale integration tests executed.
