## 19.0.0.0.12 (2026-10-02)

- Port the 18.0 fix for ticket 8970: the second transfer is created with `sudo()` (warehouse and reception type lookup, picking creation, move copy), so an operator without access rights on the receiving warehouse can validate the first leg.

## 19.0.0.0.11 (2026-10-01)

- Fix creation of the second transfer: the removed `move_ids_without_package` field is replaced by `move_ids` (TRANSIT-001).
- Fix the computed fields `is_transit_transfer` and `sub_location_existent` on multi-record sets (TRANSIT-002).
- Replace the commented-out tests with working Odoo 19 tests.

## 19.0.0.0.10 (2026-09-29)

- Own module icon, instead of the generic gears it had.
