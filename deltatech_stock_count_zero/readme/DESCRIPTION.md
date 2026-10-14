Features
========

This module adds an option to automatically set the inventoried quantity to zero when a count is requested.
This is useful during physical inventory, where items not found must be explicitly marked as zero.

Key Features
------------

- Adds the "Set Count to Zero" checkbox in the inventory request wizard.
- Automatically sets the quantity to 0.0 for the selected inventory lines when the checkbox is enabled.
- Simplifies the stock adjustment process by reducing manual input for missing items.
- Only the selected lines are set to zero: for products tracked by lot/serial number, the other lots of the product in the same location are not changed.
- The option is available to the inventory administrators only (like the standard "Set to 0").
- If a selected line was moved since it was counted, the standard conflict window opens to decide which quantity is kept.

Usage
-----

- Go to Inventory > Operations > Physical Inventory.
- Select the inventory lines and press the "Request Count" (Inventory Request) button.
- In the wizard that appears, check "Set Count to Zero".
- Upon confirmation, the system will set the inventoried quantity to zero and apply the adjustment.
