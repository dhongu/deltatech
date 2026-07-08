1. Go to **Inventory > Reporting > Adjustments > Transfer Product to Product** (menu added under Stock Adjustments).
2. In the wizard, fill in:
   - **From Product**: the product being removed.
   - **Adjustment Location**: the location to move stock from/to (acts as the counterpart location for both moves).
   - **To Product**: the product being added.
   - **Quantity**: the amount to transfer.
   - **Adjusting Location**: the location that will receive the "From Product" and give up the "To Product" (defaults to the "From Product" inventory adjustment location, and also auto-fills **Operation Type** with that location's warehouse internal transfer type).
3. If the two products have different cost prices, a warning banner shows both prices so you can double check before confirming.
4. Click **Confirm**: the wizard creates and validates two internal transfers — one moving the given quantity of the "From Product" out of stock, one moving the same quantity of the "To Product" into stock — effectively swapping one product for another without going through a manual inventory adjustment.
