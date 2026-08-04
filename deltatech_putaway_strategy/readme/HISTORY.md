# Changelog

## 19.0.1.0.5 (2026-08-04)

- Fix: restored the `Avoid Root Location on Reservation` option, which was lost
  during the 18.0 → 19.0 migration. The feature is made of two halves talking to
  each other through the `exclude_location_ids` context key: this module produces
  it in `stock.move._action_assign`, and `deltatech_stock_removal_priority`
  consumes it in `stock.quant._get_gather_domain`. Only the consumer half was
  migrated to 19.0 — the `avoid_root_location_on_reservation` field on
  `stock.picking.type` and the context injection were missing, so the key was
  never set and deliveries kept reserving stock straight from the warehouse root
  location (`lot_stock`, e.g. `D1/S`) instead of leaving it for put-away.
- The exclusion is now computed per delivery instead of per recordset. The
  previous implementation excluded the source locations of *all* outgoing
  transfers as soon as *any* of their operation types had the flag set, which
  over-excluded when `_action_assign` received moves from several operation
  types at once.
- Added regression tests covering the whole chain (flag → context → gather
  domain → reserved location), the flag-off case, and the fact that the
  exclusion applies to deliveries only.

**Upgrade note:** the field never existed in 19.0, so every operation type has
it unset after the upgrade. Tick `Avoid Root Location on Reservation` again on
the delivery operation types that need it, otherwise the behaviour stays as-is.
The option also requires `deltatech_stock_removal_priority` to be installed.
