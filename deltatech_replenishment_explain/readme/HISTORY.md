## 19.0.1.1.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

**19.0.1.1.1**

- Fix: the "rounded up to a multiple" explanation only recognized the native
  `replenishment_uom_id`, so a legacy `qty_multiple` (from the optional
  deltatech_stock_orderpoint_multiple module) rounded the quantity without any
  explanation being shown. Both sources are now considered.

**19.0.1.1.0**

- Add a visual summary to the "Why this replenishment?" dialog: an SVG quantity
  bar (forecast vs Min / Max, with the to-order gap) and a lead-horizon timeline
  (today -> lead time -> lead horizon date).

**19.0.1.0.0**

- Initial release.