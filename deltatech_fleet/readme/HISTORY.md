## 19.0.1.0.3 (2026-10-12)

- The normal consumption of a route log is recomputed when its distance or
  vehicle changes; it used to keep the value from creation, so the map sheet
  total and the reservoir level stayed wrong after editing a route.
- Opening a map sheet no longer creates an odometer reading on the vehicle.
  The odometer start used to write the end value as a side effect, and the
  next opening took that reading as start, losing the distance of the sheet.
  The readings of the sheet itself are no longer taken as the other end.
- The reservoir level includes the fuel logs and route logs not yet saved
  in the same transaction (for example when a map sheet is saved with new
  routes); it used to show the level without their consumption.
- Changing the vehicle of a map sheet moves its fuel logs, route logs and
  odometer readings to the new vehicle; they used to keep the old one.
- Moving the start of a map sheet moves its draft routes by that change
  only. The first change used to move nothing and the later ones were
  measured from the first start, so the routes drifted.
- A route log without a begin date no longer crashes on the week day.
- Map sheet default dates work for users without a time zone (UTC is used).
- Removed unused odometer methods on fuel logs and a no-op domain in the
  route log onchange.
- Tests for map sheets, fuel logs, vehicles, routes, the distance report and
  the map sheet printout.

## 19.0.1.0.2 (2026-10-09)

- New module icon (yellow car, flat Terrabit style).

## 19.0.1.0.1 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.0.0 (2026-10-08)

- Migration to 19.0: `models.Constraint` instead of `_sql_constraints`,
  `SQL()` builder for the raw queries and the cost report view,
  `_read_group` in the cost per kilometre report, `self.env._()`
  translations, company check on map sheets.

## 18.0.1.0.0 (2026-10-08)

- Migration to 18.0: `list` views, `<chatter/>`, kanban `card` template,
  `aggregator` instead of `group_operator`.
- The vehicle category (M1, N1, O1...) is now `vehicle_category_id`. The
  module used to replace the standard `category_id` of the vehicle (model
  category) with a different comodel, which broke the install on databases
  with vehicles. A migration script moves the existing values and restores
  the standard category from the vehicle model.
- The map sheet sequence gets its `fleet.map.sheet` code, so map sheets are
  numbered again instead of named "/"; a duplicated map sheet no longer fails.
- The cost report view includes the standard `vehicle_type` column.
- Access rights without a group are now given to the Fleet user group.
- Description rewritten.
