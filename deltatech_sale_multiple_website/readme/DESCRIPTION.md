eCommerce Qty Multiple
======================

This module extends the functionality of sales quantity multiples to the eCommerce platform (Odoo Website). It ensures that customers can only purchase products in specific quantity increments or meeting a minimum quantity requirement.

Key Features
============

1.  **Enforce Quantity Rules on Website**:
    *   Integrates with the `deltatech_sale_multiple` module to apply quantity constraints directly in the online store.
    *   Automatically validates the cart quantities based on the product's defined quantity multiples.

2.  **Configurable Enforcement**:
    *   Adds a "Check Min Website" option on the product template and variant forms.
    *   Allows shop managers to decide whether the minimum quantity and multiples should be strictly enforced on the website.

3.  **Enhanced Frontend Experience**:
    *   Provides visual feedback to users when they attempt to add an invalid quantity to their cart.
    *   Uses customized JavaScript components to ensure a smooth and responsive user interface during product selection.

Usage
=====

1.  Go to **Sales** or **Inventory > Products**.
2.  Open a product and go to the **Sales** tab (or wherever quantity multiples are defined).
3.  Set the **Quantity Multiple** and/or **Minimum Quantity**.
4.  Enable the **Check Min Website** checkbox to enforce these rules in the eCommerce shop.
5.  Customers browsing the website will now be restricted to selecting valid quantities for that product.
