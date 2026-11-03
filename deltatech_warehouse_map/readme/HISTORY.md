## 19.0.1.0.5 (2026-11-03)

- Description rewritten from the code: removed the Inventory > Warehouse Map
  menu and the post-init sample data, which the module does not have; the
  capacity fields are credited to `deltatech_putaway_strategy`; added a
  Limitations section.
- Banner: the capacity feature is replaced by the product list of a cell.

## 19.0.1.0.4 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.3 (2026-09-25)

- Security: the warehouse map routes are restricted to users of the
  `Inventory / User` group (others get 404), and locations and quants are read
  without `sudo()`, so access rights and multi-company rules apply.
