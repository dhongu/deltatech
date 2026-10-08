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
