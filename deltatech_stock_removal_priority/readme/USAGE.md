1. Navigate to **Inventory > Configuration > Locations**.
2. Configure **Putaway Rules** with appropriate sequence values — lower
   sequence = higher priority.
3. Go to **Inventory > Configuration > Product Categories**.
4. Set the **Removal Strategy** for the desired product categories to
   **Priority**.
5. Create a stock movement (picking) for a product in that category.
6. The system will automatically suggest picking items from the highest
   priority locations first.

Note: to set a custom default priority, go to **Settings > Technical >
System Parameters** and set the key `stock.removal_priority.default`
to the desired integer value (default: 999).
