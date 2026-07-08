On sale orders (**Sales > Orders**), this module adds stock-availability information that requires no configuration:

- **Orders list**: quotations/orders that are ready for delivery are highlighted in green, so warehouse and sales teams can spot fulfillable orders at a glance.
- **Is Ready filter**: use the quick filter in the search bar to show only orders that are ready to ship.
- **Order lines**: enable the optional **Available** column (via the list's column selector) to see, per line, the current stock situation: quantity on hand minus outgoing plus incoming, across all warehouses.

Readiness is computed automatically based on the delivery policy: for "deliver as soon as possible" orders, at least one line must have enough stock; for "deliver all at once" orders, every line must have enough stock. Once an order is confirmed, readiness instead reflects the reserved quantities on its outgoing pickings.
