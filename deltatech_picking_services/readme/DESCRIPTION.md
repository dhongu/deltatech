Besides the goods, a transfer sometimes has services tied to it, such as transport or packing. This module adds a *Services* tab to the transfer, where the operator records them with a quantity, a unit price and a subtotal.

- **Services tab**: A *Services* tab after the operations tab of every transfer lists the services in an editable list, and *Add a Service* adds a row.
- **Service lines**: Each row has a *Service* (only products of type service), a *Description* (hidden by default), a *Quantity* (1 by default), a *Unit of Measure* (for users in the units of measure group) and a *Unit Price*.
- **Defaults and totals**: Choosing a service fills in its unit of measure and description. The price is typed in, not taken from the product. The *Subtotal* is quantity times unit price, with the total shown under the column.
- **Copy and delete**: Duplicating a transfer copies its service lines, and deleting the transfer deletes them.
- **Record only**: The lines create no stock moves, invoices or accounting entries.

The module depends on *Inventory* (`stock`). Inventory users have full access to the lines, which follow a multi-company rule based on the company of their transfer. The tab has no state restriction: lines can be edited in every state of the transfer.
