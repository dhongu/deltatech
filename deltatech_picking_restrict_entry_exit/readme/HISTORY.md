# 19.0.0.0.13

- Fix (RESTRICT-001): the save-time restrictions in `write()` inspected only `move_ids_without_package`, a field
  removed from `stock.picking` in Odoo 19, so they never ran. They now read the `move_ids` commands sent by the
  picking form: CREATE commands (virtual id from the web client or `0`) are checked as new lines, falling back on
  the picking's type and locations when the line does not carry them, UPDATE commands as existing lines (against the
  demand sent in the same save, if any). Commands without values (delete, unlink, link, clear, set) are ignored
  instead of crashing.

# 19.0.0.0.12

- Fix: when several pickings were validated together, a single return or backorder in the selection exempted all
  of them from the restriction, so a receipt or delivery with a quantity above the ordered one could be validated.
  The return/backorder exemption is now checked for each picking.

# 19.0.0.0.11

- Add unit tests covering validation and save-time restrictions on receipts, deliveries and internal transfers.

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
