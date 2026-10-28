## 20.0.1.0.4 (2026-10-28)

- Migrated to Odoo 20.0. The VAT columns of the invoice analysis are added through
  `_select_list()` (the report no longer has `_select`/`_from`); the POS order analysis builds its
  query with `SQL`.

## 19.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.3 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1 (2026-08-10)

- Romanian translation for the new filters and group by entries. Without it, a user
  working in Romanian saw them in English ("Invoices for Fiscal Receipts", "Receipts
  without Invoice") and could not match them to the names used when the work was
  handed over.

## 19.0.1.0.0 (2026-08-03)

- Initial version: VAT rate and VAT tax as dimensions in Invoice Analysis and Point of
  Sale Analysis.
- `is_fiscal_receipt` flag on Invoice Analysis, with filters to show or hide invoices
  issued for an existing fiscal receipt.
- Filters for fiscal receipts with / without an invoice on Point of Sale Analysis.
