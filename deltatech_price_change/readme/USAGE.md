1. Go to **Sales > Products > Product Price Change** to open the price change documents list.
2. Create a new record, pick the **Type** (change the price directly on the product, or on a specific pricelist), optionally set a **Warehouse/Location** and, for pricelist changes, the target pricelist and validity dates.
3. Add lines for the products whose price should change: pick the product (or product template), and enter the **New Sale Price**. The **Old Sale Price** and available quantity are filled in automatically.
4. Click **Confirm**. The document is numbered and dated, the product's list price (or the pricelist item) is updated to the new price, and — for direct product price changes without a location — a child document is automatically created per warehouse for every location where the product has stock, so the price history is tracked per warehouse too.
5. Once confirmed, a price change document cannot be deleted or have its lines edited.
6. Optionally set the system parameter `price_change.public_pricelist_id` to the ID of a pricelist; when set, the price-change history printed/shown on the product only includes changes made on that pricelist.
