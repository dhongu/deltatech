1. Go to **Inventory > Configuration > Product Categories**, open the category used for pallets and enable the **Pallet** checkbox.
2. Create or edit the pallet product itself and assign it to that "Pallet" category.
3. On any product that should be sold on pallets, go to the **Palletizing** group (Inventory tab on the product form) and set:
   - **Pallet Product** – the pallet product to add to the order.
   - **Pallet Qty Min** – the minimum quantity of this product that fills one pallet.
   - The **Pallet Price** is computed automatically from the pallet product's price plus the minimum quantity times the product's price.
4. When creating or editing a sale order, once the ordered quantity of such a product reaches the minimum pallet quantity, the system automatically adds/updates a line for the required number of pallets; going past the next multiple increases the pallet quantity accordingly, and dropping below the minimum removes the pallet line again.
5. On a posted customer invoice (or credit note), use the **Show pallets status** button (top-right stat button) to open a pivot report of pallet products delivered/invoiced to that customer.
