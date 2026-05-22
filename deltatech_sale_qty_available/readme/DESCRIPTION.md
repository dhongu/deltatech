Provides real-time stock availability indicators on sales orders, helping warehouse and sales teams quickly identify which orders can be fulfilled immediately.

## Features

- **Ready indicator on list view**: Sales orders that are ready for delivery are highlighted in green in the orders list, giving an instant visual overview without opening each order.
- **Is Ready field**: A computed, stored boolean field (`is_ready`) that evaluates whether stock is available to fulfill the order based on the delivery policy:
  - *Direct policy*: at least one order line has sufficient stock on hand.
  - *One policy*: all order lines have sufficient stock on hand.
  - For confirmed orders, readiness is determined by reserved quantities on outgoing pickings.
- **Available quantity on order lines**: An optional column (`Available`) on the order line shows the current stock situation per product: virtual available = on hand − outgoing + incoming.
- **Is Ready filter**: A quick filter in the search bar lets users display only orders that are ready to ship.
- **Multi-warehouse support**: Stock availability at date is computed across all warehouses for accurate forecasting.

## Technical notes

The `is_ready` field is stored in the database and recomputed automatically when relevant data changes (state, invoice status, product stock levels, picking moves). This avoids expensive on-the-fly stock queries when loading the orders list.
