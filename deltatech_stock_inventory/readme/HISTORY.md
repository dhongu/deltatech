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
