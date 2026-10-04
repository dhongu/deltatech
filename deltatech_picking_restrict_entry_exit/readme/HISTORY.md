## 20.0.0.0.12 (2026-10-04)

- Fix: when several pickings were validated together, a single return or backorder in the selection exempted all
  of them from the restriction, so a receipt or delivery with a quantity above the ordered one could be validated.
  The return/backorder exemption is now checked for each picking.

## 20.0.0.0.11 (2026-10-04)

- Add unit tests covering validation and save-time restrictions on receipts, deliveries and internal transfers.

## 20.0.0.0.10 (2026-10-02)

- Migration to Odoo 20. No functional change: the `stock.picking` /
  `stock.move` fields and the `button_validate` / `write` hooks used by the
  module are unchanged in Odoo 20.

# 19.0.0.0.10

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.0.0.9 (2026-09-23)

- Fix: `button_validate` read `sale_line_id` / `purchase_line_id` on
  `stock.move`, but those fields are added by `sale_stock` /
  `purchase_stock`, which this module does not depend on. In a database
  where they are not installed, validating any outgoing or incoming
  picking crashed with `AttributeError: 'stock.move' object has no
  attribute 'sale_line_id'`. The checks are now skipped when the field is
  absent — without `sale_stock` / `purchase_stock` there is no order line
  a move could be linked to, so the restriction does not apply.
