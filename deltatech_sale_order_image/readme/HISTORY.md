## 19.0.1.0.1 (2026-11-17)

- Fix: the quotation / sale order PDF failed with `TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'` on databases where `sale` was not updated since the core column counter (`colspan_count`) was added on 2026-08-20. The image header now starts from the legacy column formula when the counter is missing.

## 19.0.1.0.0 (2026-11-16)

- First version. The feature moved here from `l10n_ro_sale_order_report`, which now depends on this module; the `include_image_line` company setting keeps its name and value.
