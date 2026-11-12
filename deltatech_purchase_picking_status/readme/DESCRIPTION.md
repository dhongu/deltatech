Buyers who receive goods in several deliveries need to see at a glance which purchase orders are still waiting for goods. This module adds a *Delivery Status* to purchase orders, worked out from their receipts.

- **Delivery status**: The status is *In Progress* while any receipt of the order is neither done nor cancelled, and *Done* when every receipt is done or cancelled.
- **Orders without receipts**: A confirmed order with no receipts, such as an order for services, is *Done*; before confirmation it is *In Progress*.
- **Badge and column**: The status shows as a badge on the order form and as a column, visible by default, in the RFQ and purchase order lists.
- **Filters**: Two search filters, *Done* and *In progress*, select orders by delivery status. Both skip cancelled orders.
- **On-demand status**: The status is not stored. It is worked out from the order and its receipts each time the order is opened or listed.

The module depends on `purchase_stock` and adds no groups, so anyone who can see purchase orders sees the status. A cancelled order without receipts shows *In Progress*, yet neither filter finds it.
