## 20.0.1.2.3 (2026-11-19)

- A quantity entered in the secondary unit is rounded up to a whole base unit
  only when the base unit counts pieces. For metres, kilograms or square
  metres the exact quantity is kept: with 1 bar = 5.8 m, 3 bars now give
  17.4 m instead of 18 m (#4242).

## 20.0.1.2.2 (2026-11-19)

- Documented the limitations of the secondary unit (prices, received
  quantities, stock, manufacturing, rounding) and the standard alternative of
  one real unit per factor ("Bar 6 m").

## 20.0.1.2.1 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.2.0 (2026-10-01)

- Creating, editing or deleting a product unit conversion now recomputes the
  secondary quantity of the open sale order lines, purchase order lines and
  stock moves using it. Locked or cancelled orders and done or cancelled moves
  keep the quantity computed with the previous ratio.

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
