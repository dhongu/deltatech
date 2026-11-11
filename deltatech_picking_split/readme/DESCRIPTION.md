In standard Odoo a backorder is created when a transfer is validated with less than the full quantity. This module lets the warehouse operator split a transfer by hand before that, choosing line by line what stays in the transfer and what moves to a new one, for example when only part of an order can ship today.

- **Split from the transfer**: An action in the *Action* menu of a transfer opens a window with one row per line, showing the demand and an editable *Kept* quantity.
- **Proposed quantity**: The kept quantity starts at the forecast availability of the line and can be edited.
- **New backorder transfer**: Whatever is not kept goes to a new transfer, linked to the original one as its backorder. A line with nothing kept moves whole; a line kept in part is split, and its new part is left in Draft.
- **Trace on the original**: A message with a link to the new transfer is posted on the original one.
- **Basic checks**: The window does not open for a done or cancelled transfer. A kept quantity typed below zero or above the demand is reset to the demand.

The module depends only on *Inventory* and is available to the Inventory users. If every kept quantity is zero, nothing is changed.
