## 19.0.2.7.4 (2026-08-22)

- The **delete guard** on inventory adjustments is active again: only adjustments
  in *Draft* or *Cancelled* state can be deleted. An adjustment that is *In
  Progress* or *Validated* has already generated stock moves, and deleting it
  left those moves behind without their source document. The guard existed in
  18.0 but had been commented out during the 19.0 port, so any adjustment could
  be deleted regardless of its state — silently, with no warning.
- The two documented exceptions are preserved: module uninstall
  (`_force_unlink`) and the explicit merge of adjustments, which deletes the
  merged (validated) documents with `merge_inventory=True` in the context after
  moving their lines and stock moves to the resulting adjustment.

## 19.0.2.7.3 (2026-08-15)

- Imp: `stock.inventory.line.partner_id` is now indexed — a foreign key to `res_partner` on a table that grows with every stock count.
  Context: `res_partner` is referenced by ~158 foreign-key columns; on a production database 77 of them had no index, so a single partner deletion triggered sequential scans over 3.180 MB of tables. Deleting 5.350 merged partner records took over 8 minutes without indexes and 190 seconds with them, foreign keys left ENABLED.

## 19.0.2.7.2 (2026-08-05)

- **Inventory Note** is again carried over to the generated stock move, so the
  reason of a quantity update stays visible in the product move history. The
  18.0 code wrote it to `name`, but in 19.0 the standard no longer returns a
  `name` key in `_get_inventory_move_values` — it uses `inventory_name`, which
  feeds `stock.move.reference` for inventory moves. The line had been commented
  out during a 19.0 cleanup, which silently dropped the per-line reason: the
  note could be filled in, but was stored nowhere permanent.
- The note is cleared when the adjustment is applied, so it is not silently
  reused as the reason of a later adjustment on the same quant (the standard
  `action_clear_inventory_quantity` does not reset custom fields).

## 19.0.2.7.1 (2026-08-04)

- The **Inventory Note** column in the inventory adjustment list is now shown by
  default (`optional="show"` instead of `optional="hide"`). Users had to enable
  it manually from the optional-columns menu to record why a quantity was
  changed, so in practice the reason was almost never filled in. The note is
  used as the name of the generated stock move, which makes it the only
  per-line trace of the reason in the product move history.
