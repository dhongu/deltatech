## 19.0.1.0.1

- [FIX] `sale.order.line.load()` raised `AttributeError` when importing
  without `default_order_id`/`active_id` in context (`fields.index` is a
  list method, not a dict)
- [FIX] iterating over `data` while calling `data.remove(record)` skipped
  the record right after a removed one, so some unmatched lines silently
  passed validation
