## 19.0.1.0.7 (2026-10-08)

- Fixed MRP-001: in *Production Cost Analysis*, a manufacturing order that
  consumed products from several cost categories (raw materials, packing,
  semi-finished) had its planned and produced quantities and its finished value
  multiplied by the number of categories. The consumption is now summed per
  order before joining. Finished moves with different procurement methods no
  longer duplicate the order either.

## 19.0.1.0.6 (2026-10-03)

- MRP-003 (security): the *Cost Detail* SQL view (`deltatech.cost.detail`) had no company field and no record rule, and every internal user could read it, so production cost amounts of all companies could be read directly. The view now exposes the manufacturing order company (`company_id`) with a multi-company rule, and read access is limited to Manufacturing users and Inventory users (the groups that can read manufacturing orders). Plain internal users without these groups no longer have access to the model.
- Declared the missing `stock_account` dependency: the *Cost Detail* view sums `stock_move.value`, a column added by `stock_account`, so a standalone install failed with `column sm.value does not exist`. No change on existing databases, where `stock_account` is already auto-installed with `stock` and `account`.

## 19.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
