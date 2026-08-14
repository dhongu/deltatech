## 19.0.1.0.0 (2026-08-14)

- Migrated to Odoo 19.0.
- POS JS patch adapted to the 19.0 API: `getProduct()` / `getUnit()` instead of `get_product()` / `get_unit()`,
  `price_unit` instead of the removed `get_unit_price()`, and tax mapping through
  `fiscal_position_id.getTaxesAfterFiscalPosition()` (the free `tax_utils` helper no longer exists).
- Tests adapted to the 19.0 API: `_prepare_invoice_lines()` now requires the `move_type` argument,
  the tax uses `price_include_override`, and the test partner is created locally instead of relying on demo data.
