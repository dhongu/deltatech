## 19.0.0.0.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.5 (2026-10-02)

- **Fix (BATCHTRANSFER-001): batch preparation with quantities no longer
  crashes.** The wizard read and wrote `product_uom_qty` on
  `stock.move.line`, a field removed in Odoo 19, so confirming a preparation
  with *Set Done Qty* or with product quantities raised an error and rolled
  back. The allocation now uses the Odoo 19 API: each move line can receive up
  to its reserved `quantity` (converted between the product unit and the move
  line unit), the rest is shown as additional quantity. With *Set Done Qty*
  the lines are set to the allocated quantity and marked as picked; without it
  only the requested quantities stay reserved and nothing is marked as picked.

## 19.0.0.0.4 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.0.0.3 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.
