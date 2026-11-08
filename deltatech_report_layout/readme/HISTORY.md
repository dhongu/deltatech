## 19.0.1.1.0 (2026-11-08)

- Data-only module: the empty `__init__.py` was removed, so the module has no Python
  code at all. It can be installed on Odoo Online (Custom plan) as a zip from
  Apps > Import Module, as well as on Odoo.sh and on-premise.
- The report styles are listed one by one in the manifest assets: an imported module
  does not accept wildcards (`**/*`) in asset paths.

## 19.0.1.0.2 (2026-10-16)

- Development status raised from Beta to Production/Stable: the module has been in
  production use at customers for a long time.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
