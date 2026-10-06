## 18.0.1.1.9 (2026-10-06)

- Test `test_queries_do_not_grow_with_lines` no longer counts the per-line computation of `display_qty_widget`
  (a BoM search per line in `sale_mrp`), which made it fail when `mrp` was installed; no functional change.

## 18.0.1.1.8 (2026-09-29)

- The stock colors set in Settings are applied again: the colors service imported `jsonrpc`,
  which no longer exists, so the widget silently fell back to the default colors.
- Warehouse stock is read in one batch per warehouse, not once per line and warehouse.
- Only the warehouses of the order's company are listed, and only for storable lines
  that show the availability widget.
- Warehouse and vendor quantities are shown in the unit of measure of the line.
