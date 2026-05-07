Website Sale Cost Price
========================

This module extends the standard Odoo "Prevent Sale of Zero Priced Product" functionality to also prevent sales when the product price is lower than its cost price (standard price).

Key Features:
-------------

- **Dynamic Sale Prevention**: Automatically blocks adding a product to the cart if the sale price is below the cost price.
- **Configurable Margin**: Set a minimum required margin percentage in the website settings (e.g., if set to 10%, sale price must be at least 110% of the cost price).
- **Tax-Aware Comparisons**: Configure whether the cost price includes tax or not, ensuring accurate comparison against the website sale price.
- **Currency Conversion**: Automatically handles currency differences between the product's cost currency and the website's pricelist currency.

Configuration:
--------------

1. Go to **Website > Configuration > Settings**.
2. Locate the **Shop - Checkout Process** section.
3. Enable **Prevent Sale of Zero Priced Product**.
4. Configure the new fields:
   - **Cost Price Includes Tax**: Specify if your product cost prices already include tax.
   - **Cost Price Margin %**: Set the minimum margin required for a sale to be allowed.

Usage:
------

When a user browses the website:
- If a product variant's price is lower than the calculated cost threshold, the "Add to Cart" button is replaced by the "Contact Us" button (or the action configured for zero-priced products).
- The same restriction applies to the "Quick Add" functionality.
