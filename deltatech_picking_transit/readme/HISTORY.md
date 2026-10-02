## 19.0.0.0.13 (2026-10-02)

- New option **Link Second Transfer to First** on the delivery operation type (off by default, ticket 9655). When it is
  checked, the moves of the second transfer are chained to the moves of the first one (`move_orig_ids`,
  `make_to_order`): the second transfer waits for the first, reserves exactly the delivered quantities and lots, and
  the moves are linked after the kits are exploded. A draft first transfer is confirmed when the second one is created.
- Guards on the linked second transfer (inventory, barcode and RPC validations included): it cannot be validated before
  the first transfer is done, nor receive more than was delivered, per product and lot. Partial receptions and
  backorders on both legs are allowed.
- With the option off, the behaviour is unchanged. The guards are modelled on `md_internal_warehouse_transfer`
  (MD Trade Concept SRL, Alexandru Grecu).

## 19.0.0.0.12 (2026-10-02)

- Port the 18.0 fix for ticket 8970: the second transfer is created with `sudo()` (warehouse and reception type lookup, picking creation, move copy), so an operator without access rights on the receiving warehouse can validate the first leg.

## 19.0.0.0.11 (2026-10-01)

- Fix creation of the second transfer: the removed `move_ids_without_package` field is replaced by `move_ids` (TRANSIT-001).
- Fix the computed fields `is_transit_transfer` and `sub_location_existent` on multi-record sets (TRANSIT-002).
- Replace the commented-out tests with working Odoo 19 tests.

## 19.0.0.0.10 (2026-09-29)

- Own module icon, instead of the generic gears it had.
