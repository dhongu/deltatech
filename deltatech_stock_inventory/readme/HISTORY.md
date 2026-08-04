## 19.0.2.7.1 (2026-08-04)

- The **Inventory Note** column in the inventory adjustment list is now shown by
  default (`optional="show"` instead of `optional="hide"`). Users had to enable
  it manually from the optional-columns menu to record why a quantity was
  changed, so in practice the reason was almost never filled in. The note is
  used as the name of the generated stock move, which makes it the only
  per-line trace of the reason in the product move history.
