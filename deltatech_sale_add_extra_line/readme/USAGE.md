1. On a product's form, open the **Sales** tab and fill in the **Extra Line** group:
   - **Extra Product**: the product to add automatically whenever this product is sold.
   - **Extra %**: percentage of the main line's price used to price the extra line. Leave at 0 to use the extra product's own list price instead.
   - **Extra Qty**: quantity multiplier — the extra line's quantity is the main line's quantity times this value (default 1).
2. When this product is added to a sale order (or a website/eCommerce order), the extra product line is added automatically with the computed quantity and price.
3. If you later change the quantity of the main product line, the linked extra line's quantity is recalculated automatically.
4. This works the same way through the website/eCommerce checkout (module depends on `website_sale`).
