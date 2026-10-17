## 19.0.1.0.9 (2026-10-17)

- Fixed MRP-002: in *Production Cost Analysis*, the planned quantity of a
  manufacturing order whose unit differs from the product unit (for example
  2 dozen of a product measured in units) was divided by the order unit factor
  instead of being converted, so the report showed 0.17 units instead of 24.
  The planned quantity and the planned value now use the quantity converted to
  the product unit.
- Fixed MRP-004: the *Production Cost Analysis* states and filters still used
  values from older versions (*In Production*, *Ready to Produce*, *Picking
  Exception*), so ongoing orders could not be filtered. The report now uses the
  Odoo 19 states (Draft, Confirmed, In Progress, To Close, Done, Cancelled) and
  adds the *MO Readiness* column; *Ready to Produce* and *Waiting Goods* filter
  on component readiness, *In Production* on orders in progress.

## 19.0.1.0.8 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

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
