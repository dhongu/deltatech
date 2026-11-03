## 19.0.1.0.5 (2026-11-03)

- Description rewritten after the code: the concentrations are on the BoM and the manufacturing
  order, not on the component lines; the lines get an *Ingredient Type* (Primary, Secondary, Normal).
- Documented the recalculation rule and the diluent / by-product balance; removed the traceability
  claims the code does not support.
- Added a Limitations section (form-only recalculation, same quantity on every by-product).
- Summary and Apps banner aligned with the description.

## 19.0.1.0.4 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.3 (2026-10-08)

- Fixed CONCENTRATION-001: on a manufacturing order, a concentration higher
  than the base one raised an error, because the by-product quantity was
  written on a computed field of the stock move. The by-product demand is now
  set on the move quantity.
- Fixed CONCENTRATION-002: switching a BoM or a manufacturing order between
  dilution and concentration kept the quantity of the group no longer used
  (secondary ingredient or by-product). That group is now set to zero.

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
