## 19.0.1.0.1 (2026-10-22)

- Listed on Odoo Apps as *Block Incomplete Kit Deliveries* (was *Deltatech restrict incomplete set deliveries*), with the same title on the Apps banner.
  The technical name `deltatech_mrp_set_delivery` does not change.

## 19.0.1.0.0 (2026-10-17)

- Migration to 19.0.
- The module depends on `sale_mrp`: the check reads the sale order line of the
  delivery moves, which did not exist with `mrp` alone, so validating a kit
  transfer without the Sales app installed raised an error.
- A transfer missing the first component of a restricted set showed a
  technical error instead of the "missing product" message.
- Component quantities are compared with the rounding of the unit of measure,
  so a set split with decimals is no longer refused for a rounding difference.
