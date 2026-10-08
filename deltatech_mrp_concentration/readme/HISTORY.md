## 20.0.1.0.3 (2026-10-08)

- Fixed CONCENTRATION-001: on a manufacturing order, a concentration higher
  than the base one raised an error, because the by-product quantity was
  written on a computed field of the stock move. The by-product demand is now
  set on the move quantity.
- Fixed CONCENTRATION-002: switching a BoM or a manufacturing order between
  dilution and concentration kept the quantity of the group no longer used
  (secondary ingredient or by-product). That group is now set to zero.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
