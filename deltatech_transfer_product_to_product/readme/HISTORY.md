## 19.0.0.0.5 (2026-10-17)

- Fix PRODUCTTRANSFER-002: the wizard now reserves the source product explicitly before validation, so it also works with operation types set to manual or by-date reservation, instead of failing with a zero-quantity transfer error.

## 19.0.0.0.4 (2026-10-09)

- Fix PRODUCTTRANSFER-001: the wizard validates the source leg first and returns the native backorder confirmation when only part of the quantity is available, instead of completing the replacement alone. The replacement leg is validated once the source leg is done, for the quantity actually taken out, and follows the same backorder decision (native `_create_backorder`).

## 19.0.0.0.3 (2026-10-09)

- Description corrected: the source product is taken out of stock and the destination
  product is added, as the wizard actually does.

## 19.0.0.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
