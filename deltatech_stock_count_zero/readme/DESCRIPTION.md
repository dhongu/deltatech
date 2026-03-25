Features
========

This module provides a mechanism to automatically set inventory lines to zero when an empty count is requested.
This is particularly useful during physical inventory counts where items not found should be explicitly marked as zero.

Key Features
------------

- Automatically sets the quantity to 0 when the counted quantity is left empty.
- Simplifies the inventory adjustment process by reducing manual input for missing items.
- Ensures accurate stock valuation by forcing a zero count when no items are found.

Usage
-----

- Go to Inventory > Operations > Physical Inventory.
- Start a new inventory count.
- If a product is not found, leave the counted quantity empty, and the system will treat it as zero.
