## 19.0.1.0.4 (2026-10-18)

- An invoiced POS order paid in cash with change now reconciles the payment entry with the invoice.
  The change is merged into the cash payment entry, but its negative amount also selected the
  entry's debit line; when the POS receivable account is the customer's receivable account (4111 in
  the Romanian chart), the debit and the credit of the payment entry were reconciled with each other
  and the invoice stayed unpaid. The merged change no longer selects lines for the invoice
  reconciliation.

## 19.0.1.0.3 (2026-10-17)

- The global discount line (`pos_discount`) is no longer passed through the fiscal position a second
  time: like in core, it keeps the already mapped taxes of the lines it discounts, so with chained
  mappings (A to B, B to C) the discount is no longer taxed with C and its price is not adapted again
  (#3414).

## 19.0.1.0.2 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0 (2026-08-14)

- Migrated to Odoo 19.0.
- POS JS patch adapted to the 19.0 API: `getProduct()` / `getUnit()` instead of `get_product()` / `get_unit()`,
  `price_unit` instead of the removed `get_unit_price()`, and tax mapping through
  `fiscal_position_id.getTaxesAfterFiscalPosition()` (the free `tax_utils` helper no longer exists).
- Tests adapted to the 19.0 API: `_prepare_invoice_lines()` now requires the `move_type` argument,
  the tax uses `price_include_override`, and the test partner is created locally instead of relying on demo data.
- Fiscal position mapping in the test now uses `original_tax_ids` on the destination tax;
  the `account.fiscal.position.tax` model (`tax_src_id` / `tax_dest_id`) no longer exists in 19.0.
