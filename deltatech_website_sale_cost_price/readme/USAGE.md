Configuration:

1. Go to **Website > Configuration > Settings**.
2. Locate the **Shop - Checkout Process** section.
3. Enable **Prevent Sale of Zero Priced Product**.
4. Configure the new fields:
   - **Cost Price Includes Tax**: specify if your product cost prices already include tax.
   - **Cost Price Margin %**: set the minimum margin required for a sale to be allowed (e.g. 10% means the sale price must be at least 110% of the cost price).

Usage:

When a visitor browses the website:

- If a product variant's price is lower than the calculated cost threshold (cost price plus the configured margin, with currency and tax handled automatically), the "Add to Cart" button is replaced by the "Contact Us" button (or whichever action is configured for zero-priced products).
- The same restriction applies to the "Quick Add" functionality.
