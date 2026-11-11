Sales teams need to see which sales orders still have deliveries to make. This module adds a *Picking Status* to sales orders, worked out from the order's transfers, with two values: *In Progress* and *Done*.

- **Open or closed**: A confirmed order is *In Progress* while any of its transfers is neither done nor cancelled, and *Done* when every transfer is done or cancelled. A quotation, draft or sent, is *In Progress*.
- **No transfers**: A confirmed order with no transfers, for example when it holds only services, stays *In Progress*.
- **Cancelled orders**: A cancelled order shows *Done*, even if nothing was delivered.
- **Badge and column**: The status shows as a badge on the order form and as a column, visible by default, in the quotation and order lists.
- **Filters**: Two search filters, *Done* and *In progress*, select orders by this status.
- **Automatic update**: The status is stored and follows the order's state and transfers. It is also refreshed when a transfer is confirmed, reserved, cancelled or validated, and each change is tracked in the order's chatter.

The module depends on `sale_stock` and adds no groups, so anyone who can see sales orders sees the status. It has only two values, so it does not tell a partial delivery from one that has not started.
