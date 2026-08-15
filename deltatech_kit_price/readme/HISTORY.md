# Changelog

## 19.0.0.0.2 (2026-08-15)

- Fix: added the missing `mrp_account` dependency. `_compute_purchase_price()`
  calls `product.product._compute_bom_price()`, which is defined in
  `mrp_account`. Since `mrp_account` is `auto_install` and Odoo 19 test
  databases are built with `--skip-auto-install`, the module only worked when
  another addon in the same database required `mrp_account` explicitly
  (`deltatech_mrp_cost` did). Installed on its own, both tests failed with
  `AttributeError: 'product.product' object has no attribute
  '_compute_bom_price'`.
