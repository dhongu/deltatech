## 19.0.1.0.4 (2026-11-03)

- Description and banner rewritten after the code: the lines open from the **Order lines**
  smart button in a separate list, not in a section of the form; the import loads sales order
  lines, not purchase lines; documented how existing lines are matched and updated.

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
