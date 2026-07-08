1. Go to **Purchase > Configuration > Settings** and configure the price update
   behavior for goods receipts:
   - **Update product supplier price** — always overwrite the vendor's price
     (in `product.supplierinfo`) with the price from the purchase order.
   - **Update list price** — update the sales price according to the trade
     markup and the last purchase price.
   - **Add supplier to product** — automatically add the vendor and its price
     to the product's vendor list when a purchase order is confirmed.
   - **Force price at validation** — (re)apply the price at both PO validation
     and vendor bill validation.
2. Validate a goods receipt: the product's **Last Purchase Price** field
   (Purchase tab of the product form) is updated automatically, and
   `standard_price` / vendor prices / list price are refreshed according to
   the settings above.
3. To set a markup used to compute the sales price from the last purchase
   price, select one or more products in the Products list, open **Action >
   Set Trade Markup**, enter the **Trade Markup** value and click **Set**. Use
   the wizard's **Partner** option (instead of the selected products) to apply
   the markup to every product supplied by a given vendor.
