# Changelog

## 19.0.1.0.1 (2026-09-23)

- Fix: the tests validated an outgoing picking that is deliberately not
  linked to a sale order, which `deltatech_picking_restrict_entry_exit`
  forbids. `test_user_with_access_can_validate` and
  `test_warehouse_without_users_is_not_restricted` therefore failed
  whenever both modules were installed in the same database, such as on a
  full-suite CI run. The test users are now added to that module's bypass
  group when it is present, so the tests stay about warehouse access only.
