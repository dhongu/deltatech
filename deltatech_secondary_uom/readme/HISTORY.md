## 19.0.1.1.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.1.0 (2026-08-06)

- Quantities entered in a secondary unit are rounded **up** to whole base
  units (no fractional pieces); the secondary quantity is recomputed from the
  rounded piece count.
- The secondary unit is propagated from the sale order line to the delivery
  move and from the purchase order line to the receipt move.

## 19.0.1.0.0 (2026-08-06)

- Initial version: product UoM conversion table (SAP MARM style), secondary
  quantity/unit on sale order lines, purchase order lines and stock moves.
