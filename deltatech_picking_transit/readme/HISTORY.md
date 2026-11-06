## 20.0.0.0.16 (2026-11-06)

- Port of 19.0.0.0.15 (TRANSIT-003): opening or reloading a transit delivery no longer
  locks or unlocks it; the lock changes only with the native Lock / Unlock button.
  The limitation is removed from the description.

## 20.0.0.0.15 (2026-11-03)

- Description rewritten from the code: the operation type field is Two Step
  Transfer Use (Delivery / Reception), not "next operation"; the original
  transfer is not locked after the second one is created.
- Documented the checks on reception, the backorder handling and the optional
  Reassign Location button, and the lock switching of a Delivery transfer on
  20.0.
- Summary and banner corrected.

## 20.0.0.0.14 (2026-10-10)

- Fix partial deliveries with a backorder (TRANSIT-004): the receiving leg checks its products against the source transfer and all its backorders, so the products left for a source backorder can still be received. A source backorder created by the native `_create_backorder` keeps "Second Transfer Created" (its products are already in the receiving leg, no duplicate reception) and its chatter names the receiving transfer.

## 20.0.0.0.13 (2026-10-09)

- Apps Store banner (banner.json).

## 20.0.0.0.12 (2026-10-02)

- Port the 18.0 fix for ticket 8970: the second transfer is created with `sudo()` (warehouse and reception type lookup, picking creation, move copy), so an operator without access rights on the receiving warehouse can validate the first leg.

## 20.0.0.0.11 (2026-10-01)

- Migration to Odoo 20: access rights moved to `ir.access`, the `use_sub_locations`
  setting is read with `ir.config_parameter.get_bool`.

## 19.0.0.0.11 (2026-10-01)

- Fix creation of the second transfer: the removed `move_ids_without_package` field is replaced by `move_ids` (TRANSIT-001).
- Fix the computed fields `is_transit_transfer` and `sub_location_existent` on multi-record sets (TRANSIT-002).
- Replace the commented-out tests with working Odoo 19 tests.

## 19.0.0.0.10 (2026-09-29)

- Own module icon, instead of the generic gears it had.
