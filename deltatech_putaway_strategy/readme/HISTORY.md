# Changelog

## 18.0.1.0.6 (2026-08-04)

- Development status raised from *Beta* to *Production/Stable*. The module is consumed by
  `deltatech_stock_barcode`, which is itself published as *Production/Stable*; `manifestoo
  check-dev-status` rejects a module that is more mature than one of its dependencies, and
  that check blocked the whole test job on the 18.0 branch. No functional change.
