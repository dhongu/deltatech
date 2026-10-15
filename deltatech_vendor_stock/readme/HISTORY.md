## 20.0.1.2.0 (2026-10-15)

Port of 19.0.1.1.12 and 19.0.1.2.0:

- The availability popover shows the vendor stock and the stock per warehouse again: the widget
  now loads the fields it reads itself instead of relying on columns declared in the order line
  view.
- The unit of measure is shown again next to the quantities in the popover (many2one values are
  objects, so `product_uom_id[1]` was empty).
- The free stock per warehouse is listed as a table, read when the popover opens instead of for
  every order line: the warehouse of the order comes first, is marked and is shown even without
  stock; each warehouse shows its code and name.
- Quantities that cover the quantity to deliver are green; the order warehouse is red when it does
  not cover it.
- A click on a warehouse opens the forecast of the product in that warehouse.
- The vendor stock is shown under the warehouses, and only when it is not zero.
- Romanian translations for the popover and the settings; "Other Stock" is now "Alt stoc".

## 20.0.1.1.11 (2026-10-09)

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
