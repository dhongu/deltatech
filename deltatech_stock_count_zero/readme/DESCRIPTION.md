Features
========

This module adds an option to automatically set the inventoried quantity to zero when a count is requested.
This is useful during physical inventory, where items not found must be explicitly marked as zero.

Key Features
------------

- Adds the "Set Count to Zero" checkbox in the inventory request wizard.
- Automatically sets the quantity to 0.0 for the selected inventory lines when the checkbox is enabled.
- Simplifies the stock adjustment process by reducing manual input for missing items.

Usage
-----

- Go to Inventory > Operations > Physical Inventory.
- Select the inventory lines and press the "Request Count" (Inventory Request) button.
- In the wizard that appears, check "Set Count to Zero".
- Upon confirmation, the system will set the inventoried quantity to zero and apply the adjustment.
