Managers often need to know how much came in from a supplier, or what went out to a customer, over a period. This module adds a *Picking Analysis* report on done transfers, as a pivot table and as a list.

- **Done moves only**: Each row is one transfer, product, source location and destination location, built from done stock moves. Moves outside a transfer are left out.
- **Signed quantity and amount**: *Quantity* is the processed quantity in the unit of measure of the product. *Amount* is the value stored on the stock move, or quantity times the move's unit price when none is stored. Both are positive when the destination is an internal location (also for moves between two internal locations) and negative otherwise.
- **Pivot and list**: The pivot opens grouped by *Picking Type*, then *Commercial Entity*; rows also show the *Partner* of the transfer. The list totals quantity and amount, with *Date*, *Location*, *Location Destination* and *Category* as optional columns.
- **Filters and grouping**: The *Incoming*, *Internal* and *Outgoing* filters select by operation type, and the date filter uses the date the transfer was done. Rows can also be grouped by product, category, partner, location, destination location or date.

The module depends on `stock_account`. It is read-only and open only to stock managers (`stock.group_stock_manager`). Users see only transfers of their active companies.
