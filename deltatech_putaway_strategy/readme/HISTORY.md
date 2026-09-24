# Changelog

## 19.0.1.1.0 (2026-09-24)

- New option: prefer the shelf where the product is already stocked. When the system parameter
  `deltatech_putaway_strategy.prefer_existing_stock_location` is `True`, the putaway looks for the
  leaf locations under the incoming location (e.g. `D1/S`) that already hold the product and
  proposes the one with the largest quantity that still has capacity, even when it is not under
  the location given by the putaway rule. This covers products moved physically to another shelf
  without updating their rule: the rule kept sending them to the old shelf, and
  `search_sublocation` could not reach the new one because it only looks below the rule's
  location. The rule's location still wins when it already holds the product, the incoming
  location itself is ignored (goods not yet put away) and a full shelf falls back to the usual
  strategy. Disabled by default, so existing installations keep their behaviour.
- A shelf is never proposed as the destination of the goods leaving it: only free stock
  (quantity minus reserved) counts, and the source locations of the move lines are passed to the
  putaway through the `putaway_exclude_location_ids` context key, so a transfer from a shelf is
  not sent back to that same shelf even when stock remains there.

## 19.0.1.0.7 (2026-08-04)

- Development status raised from *Beta* to *Production/Stable*. The module is consumed by
  `deltatech_stock_barcode`, which is itself published as *Production/Stable*; `manifestoo
  check-dev-status` rejects a module that is more mature than one of its dependencies. No
  functional change.

## 19.0.1.0.6 (2026-08-04)

- Fix: a plain stock user (`stock.group_stock_user`) could not validate a transfer into a
  location that has a capacity configured — it failed with
  `AccessError: You are not allowed to modify 'Inventory Locations' (stock.location)`,
  pointing at Inventory/Administrator. `current_products`, `max_products`,
  `planned_products` and `occupancy_ratio` are **non-stored** computed fields, and
  `_action_done` / `_split_by_putaway_capacity` invoked their compute methods *directly*.
  Outside the ORM's compute machinery the assignments inside those methods no longer just
  fill the cache — they become a real `write()` on `stock.location`, which only the
  inventory administrator may perform. Both call sites now invalidate the cache and let the
  ORM compute on read instead, on a `sudo()` recordset (these are metrics derived from
  quants, already read with sudo inside the compute, not business data).
- The over-capacity barrier is unchanged: exceeding a location's capacity still raises the
  usual `UserError`, now reachable by stock users instead of being masked by an
  `AccessError`.
- Fix: the value was previously read from a different environment than the one the compute
  had been invoked on, so the manual call was dead work and, in
  `_split_by_putaway_capacity`, the `exclude_move_line_id` context key had no effect at all.
  Reading now happens on the same recordset the context is applied to.
- Added regression tests: a stock user validating into a capacity-limited location, the
  over-capacity barrier still raising a business error, and reading the occupancy metrics
  without administrator rights.

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
