Managers often need to know how much came in from a supplier, or what went out to a customer, over a period. This module adds a *Picking Analysis* report on done transfers, as a pivot table and as a list.

- **Done and valued moves**: Each row is one transfer, product, source location and destination location, built from done stock moves that have a stock valuation layer. Moves outside a transfer are left out.
- **Signed quantity and amount**: *Quantity* is the demand of those moves in the unit of measure of the product, positive when the destination is an internal location and negative otherwise. *Amount* is the total value of their valuation layers, so receipts are positive and deliveries negative.
- **Pivot and list**: The pivot opens grouped by *Picking Type*, then *Commercial Entity*. The list also shows the *Partner* of the transfer and totals quantity and amount, with *Date*, *Location*, *Location Destination* and *Category* as optional columns.
- **Filters and grouping**: The *Incoming*, *Internal* and *Outgoing* filters select by operation type, and the date filter uses the creation date of the transfer. Rows can also be grouped by product, category, partner, location, destination location or date.

The module depends on `stock_account`. It is read-only and open only to stock managers (`stock.group_stock_manager`).
