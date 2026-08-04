## 18.0.1.0.1 (2026-08-04)

- The tests read the report with `sudo()`: they check the content of the report, not
  its visibility, so a module such as `deltatech_restrict_reports` (which hides the
  report from users outside its access groups with a global `ir.rule`) no longer makes
  them fail when installed in the same database.

## 18.0.1.0.0 (2026-08-03)

- Initial version: VAT rate and VAT tax as dimensions in Invoice Analysis and Point of
  Sale Analysis.
- `is_fiscal_receipt` flag on Invoice Analysis, with filters to show or hide invoices
  issued for an existing fiscal receipt.
- Filters for fiscal receipts with / without an invoice on Point of Sale Analysis.
