## 19.0.1.0.5 (2026-11-27)

- [FIX] Import into an order with lines no longer crashes with `Expected singleton` when the
  product is on several lines (#3510). The rows keep their ID / External ID when the file has
  them; otherwise the description narrows the match, and a row that still matches several
  lines, or a product with more rows than lines, is reported as an import error (next to the
  Product column of the import screen) instead of being assigned to an arbitrary line.
- [FIX] The lines named by an External ID are taken before the rows without ID, and two rows
  with the same ID are an error, so a line is updated by one row at most. An ID that is not a line
  of the order (deleted after the export, or from another order's file) is an error too, instead of
  creating a line or changing the other order.
- [FIX] The order read from the **Order Reference** column (import without the **Order lines**
  button) is found by its reference or database id; the text `39` no longer opened orders 3 and 9.
- The **Order Lines** list shows the **Description** column.
- Consultant sheet (`readme/FISA_CONSULTANT.md`), `readme/USAGE.md` and screenshots generated
  by `tests/test_screenshots.py`; the **Order lines** button and the **Order Lines** list are
  translated in Romanian.

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
