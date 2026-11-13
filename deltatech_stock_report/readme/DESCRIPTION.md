Managers often need to know how much came in from a supplier, or what went out to a customer, over a period. This module adds a *Picking Analysis* report on done transfers, as a pivot table and as a list.

- **Done moves only**: Each row is one transfer, product, source location and destination location, built from done stock moves. Moves outside a transfer are left out.
- **Signed quantity and positive amount**: *Quantity* is the demand of the move, not the quantity processed, in the unit of measure of the product. It is positive when the destination is an internal location (also for moves between two internal locations) and negative otherwise. *Amount* is the value stored on the stock move, or quantity times the move's unit price when none is stored. Receipts and deliveries both show a positive amount.
- **Pivot and list**: The pivot opens grouped by *Picking Type*, then *Commercial Entity*. The list shows the *Partner* of the transfer, totals quantity and amount, and has *Date*, *Location*, *Location Destination* and *Category* as optional columns.
- **Filters and grouping**: The *Incoming*, *Internal* and *Outgoing* filters select by operation type, and the date filter uses the date the transfer was done. Rows can also be grouped by product, category, partner, location, destination location or date.

The module depends on `stock_account`. It is read-only and open only to stock managers (`stock.group_stock_manager`). Users see only transfers of their active companies.
