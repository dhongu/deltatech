## Viewing invoice history on a product

1. Go to **Inventory** (or **Sales** / **Purchase**) and open any product.
2. Click the **History** tab.
3. The table shows one row per year with **Qty In** (purchase invoices) and
   **Qty Out** (sales invoices) totals for that product.
4. Click the **Refresh** button (circular arrow icon) to recompute the history
   immediately from all posted invoices for this product.

## Opening the Invoice Analysis report for a product

1. From the product form, click the **View Invoices** button (available on both
   the product template and the product variant form).
2. The **Invoice Analysis** report opens pre-filtered to the selected product
   and pre-grouped by year, with move type as a column group.

## Using the extended Invoice Analysis report

1. Go to **Accounting > Reporting > Invoice Analysis**
   (or use the standard Invoice Analysis menu).
2. Use the new **Region** group-by filter to aggregate invoices by the customer
   or supplier's state/region.
3. The **Default Supplier** column is available in the pivot/graph view to
   identify the primary supplier assigned to each product.

## Automatic daily refresh

The cron job **Update Product Invoice History by Year** runs once per day and
recomputes the history table for all products. No manual action is required for
routine updates.
