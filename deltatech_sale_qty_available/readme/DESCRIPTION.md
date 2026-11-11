Salespeople and warehouse staff need to see at a glance which orders can ship. This module computes an *Is ready* flag for open quotations and sales orders and shows the ready ones in green in their lists.

- **Green rows**: The quotation and sales order lists show a ready order in green. An *Is Ready* filter in the order search returns the ready ones.
- **Quotations**: A draft or sent quotation is ready when stock on hand minus outgoing quantity covers the quantity left to deliver on every line, or on at least one line when the `picking_policy` is `direct`.
- **Confirmed orders**: A confirmed order is ready when its transfers have reserved stock: any reserved move under `direct`, every move of the transfers not yet done otherwise. Orders stay ready after delivery until fully invoiced; cancelled ones never are.
- **Available column**: An optional *Available* column on the order lines, hidden by default and shown to Inventory users, gives the forecast with its on hand, outgoing and incoming parts, or *N/A* when all are zero. It reads the source location of the line's route, when it has one.

It depends on `sale_stock`. The flag is stored on the order and can be searched. The module also sets the context key `all_warehouses` when the quantity at date of an order line is computed.
