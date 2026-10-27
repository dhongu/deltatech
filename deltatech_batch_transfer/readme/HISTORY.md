## 20.0.0.0.8 (2026-10-22)

- Listed on Odoo Apps as *Batch Transfer Extension* (was *Batch Transfer*). The technical name `deltatech_batch_transfer` does not change.

## 20.0.0.0.7 (2026-10-16)

Migration to 20.0:

- `stock_picking_batch` is merged into `stock`: the dependency is dropped and the views,
  actions and the report binding point to `stock`.
- The "Received" page and its move line list decoration use the batch move line list
  (`stock.stock_move_line_view_list_from_batch`), so the generic move line list is not changed.
- The `deltatech_batch_keep_pickings` system parameter is read with `get_bool`.
- The batch preparation wizard uses the move line `uom_id` and the unit `compare()` API.
- Access rights are declared in `ir.access`.

## 19.0.0.0.7 (2026-10-11)

- Docs: emoji symbols added to the bold headings of the module description, for a uniform look on the Odoo Apps page. No code change.

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
