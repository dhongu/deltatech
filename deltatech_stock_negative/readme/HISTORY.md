## 19.0.2.0.8 (2026-09-22)

- **Several lines of one validation no longer share the same stock.** The check
  runs over the whole recordset before `super()._action_done()` writes anything
  to the quants, so every line used to read the same untouched quantity. Taken
  one by one, two lines of 1 against a stock of 1 are each legal, and the
  transfer still landed at -1. It now carries what the earlier lines of the same
  batch already took from each quant, keyed by product, location, lot, package
  and owner -- so lines on different quants still do not add up.
  Reported twice from the shop floor: 2 pieces picked to shelve when only 1 was
  on hand.
