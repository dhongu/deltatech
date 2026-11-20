## 19.0.1.0.1 (2026-11-20)

- The line price now takes the `BaseQuantity` of the UBL price into account (`cac:Price`): a
  price of 50 declared for 100 units is read as 0.50 per unit, also when the base unit differs
  from the unit of the invoiced quantity. A missing, zero, negative or unreadable base is taken
  as 1, as before. The line discount is computed on the normalised price. Fixes #3590.

## 19.0.1.0.0 (2026-11-19)

- Initial release: the UBL parser, vendor lookup, product matcher, unit conversion, vendor
  price update and duplicate bill lookup moved out of `deltatech_purchase_ubl`, so that they
  can be used without the purchase and stock apps.
