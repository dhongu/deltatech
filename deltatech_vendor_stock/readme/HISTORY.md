## 19.0.1.1.12 (2026-10-15)

- The availability popover shows the vendor stock and the stock per warehouse again: the widget
  now loads these fields itself instead of relying on columns declared in the order line view.
- The unit of measure is shown again next to the quantities in the popover (many2one values are
  objects in 19.0, so `product_uom_id[1]` was empty).
- Each warehouse is listed on its own line in the popover.

## 19.0.1.1.11 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.1.10 (2026-09-29)

- The stock colors set in Settings are applied again: the colors service imported `jsonrpc`,
  which no longer exists, so the widget silently fell back to the default colors.
- Warehouse stock is read in one batch per warehouse, not once per line and warehouse.
- Only the warehouses of the order's company are listed, and only for storable lines
  that show the availability widget.
- Warehouse and vendor quantities are shown in the unit of measure of the line.

## 19.0.1.1.9 (2026-09-29)

- Own module icon, instead of the generic gears it had.
