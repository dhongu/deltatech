## 19.0.1.0.3

- Add unit tests covering the order lines action and the Excel import preprocessing of sale order lines (update existing lines, add lines to an empty order, order taken from the order_id column).

## 19.0.1.0.2

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.1

- [FIX] `sale.order.line.load()` raised `AttributeError` when importing
  without `default_order_id`/`active_id` in context (`fields.index` is a
  list method, not a dict)
- [FIX] iterating over `data` while calling `data.remove(record)` skipped
  the record right after a removed one, so some unmatched lines silently
  passed validation
