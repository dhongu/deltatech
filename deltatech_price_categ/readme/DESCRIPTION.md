Price Category
==============

This module introduces a tiered pricing system for products in Odoo, allowing businesses to define multiple price levels (Bronze, Copper, Silver, and Gold) based on configurable percentage markups from a base price.

Key Features
============

1.  **Tiered Pricing Structure**:
    *   Adds fields for **Bronze**, **Copper**, **Silver**, and **Gold** percentage markups on the product template.
    *   Automatically computes the corresponding prices based on the selected base price.

2.  **Flexible Base Price Selection**:
    *   Choose between **List Price**, **Cost Price**, or **Last Purchase Price** as the foundation for markup calculations.
    *   Handles tax-included or tax-excluded prices gracefully during computation.

3.  **Pricelist Integration**:
    *   Extends Odoo's standard pricelist items to include these new price tiers as base options.
    *   Allows for dynamic pricing rules that reference the computed Bronze, Silver, etc., prices.

4.  **Price Issue Monitoring**:
    *   Includes a calculated field to detect inconsistencies in the price hierarchy (e.g., if a Gold price is higher than a Silver price).

Usage
=====

1.  Open a **Product Template** and navigate to the **Sales** or **Inventory** tab where the new price fields are located.
2.  Select the **Base Price** method (List Price, Cost, or Last Purchase).
3.  Enter the percentage markups for each tier (Bronze Percent, Silver Percent, etc.).
4.  The system will automatically compute and display the resulting tier prices.
5.  In **Pricelists**, you can now create items that use these calculated prices as a base for further discounts or rules.
