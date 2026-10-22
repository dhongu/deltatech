# 19.0.1.0.3 (2026-10-17)

- Setting a dimension to zero now resets the volume to zero, instead of keeping the
  previous value.
- The volume computed from the dimensions is now expressed in the configured volume
  unit: with volumes in cubic feet, 100 x 100 x 100 cm gives about 35.31 ft³, not 1.

# 19.0.1.0.2 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

# 19.0.1.0.1

- Own module icon, instead of the generic gears it had.

# Changelog

## 19.0.1.0.4 (2026-10-22)

- Listed on Odoo Apps as *Product Dimensions* (was *Products Dimension*). The technical name `deltatech_product_dimension` does not change.

## [19.0.1.0.0] - 2026-06-15

### Changed

- Ported to Odoo 19.0. Fully aligned with 18.0: fields `product_length`, `product_width`, `product_height`, `_onchange_dimension`, views, tests, and i18n/ro.po are all present and equivalent.
