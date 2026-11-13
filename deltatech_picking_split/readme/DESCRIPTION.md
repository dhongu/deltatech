In standard Odoo a backorder is created when a transfer is validated with less than the full quantity. This module lets the warehouse operator split a transfer by hand before that, choosing line by line what stays in the transfer and what moves to a new one, for example when only part of an order can ship today.

- **Split from the transfer**: An action in the *Action* menu of a transfer opens a window with one row per line, showing the *Demand* and an editable *Kept* quantity.
- **Proposed quantity**: The window proposes the forecast availability of each line as the kept quantity. You can change it before applying.
- **New backorder transfer**: Whatever is not kept goes to a new transfer in Draft, linked to the original one as its backorder. A line with nothing kept moves whole; a line kept in part is split.
- **Trace on the original**: A message with a link to the new transfer is posted on the original one.
- **Safeguards**: The window refuses a kept quantity below zero or above the demand, a line that no longer belongs to the transfer, and a transfer that is already done or cancelled.

The module depends only on *Inventory* and is available to the Inventory users. The new transfer is left in Draft and is not reserved automatically. At least one line must keep some quantity: if every kept quantity is zero, nothing is changed.
