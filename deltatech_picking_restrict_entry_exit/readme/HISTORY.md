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
