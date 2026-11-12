Sales teams need to see which sales orders still have deliveries to make. This module adds a *Picking Status* to sales orders, worked out from their transfers, with two values: *In Progress* and *Done*.

- **Open or closed**: A confirmed order is *In Progress* while any transfer is neither done nor cancelled, and *Done* when every transfer is done or cancelled. New orders start as *In Progress*.
- **No transfers**: A confirmed order with no transfers, for example one that holds only services, stays *In Progress*.
- **Cancelled orders**: An order whose transfers are all cancelled shows *Done*, even if nothing was delivered.
- **Badge and column**: The status shows as a badge on the order form and as a column, visible by default, in the quotation and order lists.
- **Filters**: Two search filters, *Done* and *In progress*, select orders by this status.
- **When it updates**: The status is stored and recalculated only when one of the order's transfers is confirmed, reserved, cancelled or validated. Each change is tracked in the order's chatter.

The module depends on `sale_stock` and adds no groups, so anyone who can see sales orders sees the status. Changes to the order itself, such as reopening it, do not refresh it. It cannot tell a partial delivery from one not started.
