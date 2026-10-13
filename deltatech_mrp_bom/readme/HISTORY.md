## 19.0.1.0.7 (2026-10-08)

- Fixed MRPBOM-001: a derived BoM was created with quantity 1 regardless of the
  base BoM yield, so a base making 10 units from 20 components consumed 200 for
  an order of 10. The derived BoM now copies the base quantity and unit, the
  operations (with their dependencies) and the by-products. Lines, operations
  and by-products restricted to other variants are no longer copied, and
  recomputing a derived BoM archives its previous operations instead of
  leaving the work orders of existing orders without operation.

## 19.0.1.0.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.
