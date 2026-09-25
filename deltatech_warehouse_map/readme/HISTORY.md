## 19.0.1.0.3 (2026-09-25)

- Security: the warehouse map routes are restricted to users of the
  `Inventory / User` group (others get 404), and locations and quants are read
  without `sudo()`, so access rights and multi-company rules apply.
