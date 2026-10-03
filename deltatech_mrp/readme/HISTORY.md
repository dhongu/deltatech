## 19.0.1.0.6 (2026-10-03)

- MRP-003 (security): the *Cost Detail* SQL view (`deltatech.cost.detail`) had no company field and no record rule, and every internal user could read it, so production cost amounts of all companies could be read directly. The view now exposes the manufacturing order company (`company_id`) with a multi-company rule, and read access is limited to Manufacturing users and Inventory users (the groups that can read manufacturing orders). Plain internal users without these groups no longer have access to the model.

## 19.0.1.0.5 (2026-09-29)

- Own module icon, instead of the generic gears it had.
