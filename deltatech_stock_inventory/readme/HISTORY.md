## 18.0.2.6.2 (2026-08-17)

- The **Inventory Note** is cleared when the adjustment is applied, so it is not
  silently reused as the reason of a later adjustment on the same quant. The
  standard `action_clear_inventory_quantity` does not reset custom fields, so a
  note left over from a previous count became the reference of the next stock
  move without the operator noticing.
- Adds the missing Romanian translation of the column label ("Notă inventar"),
  which was shown in English to operators, and tests for both behaviours.

## 18.0.2.6.1 (2026-08-03)

- The **Inventory Note** column in the inventory adjustment list is now shown by
  default (`optional="show"` instead of `optional="hide"`). Users had to enable
  it manually from the optional-columns menu to record why a quantity was
  changed, so in practice the reason was almost never filled in. The note is
  used as the name of the generated stock move, which makes it the only
  per-line trace of the reason in the product move history.
