In standard Odoo a backorder is created when a transfer is validated with less than the full quantity. This module lets the warehouse operator split a transfer by hand before that, choosing line by line what stays in the transfer and what moves to a new one, for example when only part of an order can ship today.

- **Split from the transfer**: An action in the *Action* menu of a transfer opens a window with one row per line, showing the demand and an editable **Kept** quantity.
- **Sensible default**: The proposed kept quantity is the available or the reserved quantity, whichever is higher, converted to the unit of measure of the line and never below zero or above the demand.
- **New backorder transfer**: Whatever is not kept goes to a new transfer, created as a copy of the original and linked to it as its backorder. A line with nothing kept moves whole; a line kept in part is split, and its new part starts in Draft.
- **Trace on the original**: A message with a link to the new transfer is posted on the original one.
- **Safeguards**: The window refuses a kept quantity below zero or above the demand, a line that no longer belongs to the transfer, and a transfer that is already done or cancelled.

The module depends only on *Inventory* and is available to the Inventory users. It does not reserve the new transfer. At least one line must keep some quantity: if every kept quantity is zero, nothing is changed.
