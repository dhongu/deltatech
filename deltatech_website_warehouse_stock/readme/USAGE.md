1. Go to **Website > Configuration > Settings** and set the **Stock Threshold** (default 10) under the warehouse stock display option — this is the quantity above which a warehouse is shown as "Available" instead of showing the exact count.
2. Go to **Inventory > Configuration > Warehouses**, open a warehouse and use the **Display on Website** checkbox to decide whether that warehouse's stock should appear on the product page at all.
3. On the website product template page, each enabled warehouse then shows one of:
   - "Out of stock" if the stock is negative,
   - the exact quantity if it is between 0 and the threshold,
   - "Available" if it is above the threshold.

The warehouse name shown on the website is the same name configured on the warehouse record.
