## 20.0.0.0.11 (2026-10-01)

- Migration to Odoo 20: access rights moved to `ir.access`, the `use_sub_locations`
  setting is read with `ir.config_parameter.get_bool`.

## 19.0.0.0.11 (2026-10-01)

- Fix creation of the second transfer: the removed `move_ids_without_package` field is replaced by `move_ids` (TRANSIT-001).
- Fix the computed fields `is_transit_transfer` and `sub_location_existent` on multi-record sets (TRANSIT-002).
- Replace the commented-out tests with working Odoo 19 tests.

## 19.0.0.0.10 (2026-09-29)

- Own module icon, instead of the generic gears it had.
