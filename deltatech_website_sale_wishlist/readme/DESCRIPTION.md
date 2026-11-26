eCommerce Wishlist Extension
============================

This module extends the standard Odoo eCommerce wishlist functionality by providing backend management and actionable insights into products that customers are interested in but have not yet purchased.

Key Features
============

1.  **Backend Wishlist Visibility**:
    *   Adds a dedicated **Wishlists** menu under *Website > eCommerce > Products*.
    *   Provides a structured list and form view of all wishlist items across the entire platform.
    *   Allows administrators to see which partners have added which products to their wishlists.

2.  **Stock Awareness**:
    *   Displays the **Quantity On Hand** of each product on a wishlist, computed when the list is shown, as the total stock of the warehouses of the companies selected in the company switcher (replenishment goes to the user's default warehouse).
    *   Helps inventory managers identify demand for out-of-stock items.

3.  **One-Click Replenishment**:
    *   Select wishlist lines in the list view and click **Replenish**.
    *   Each selected line procures one unit of its product in the user's default warehouse, through the product route (a request for quotation with *Buy*, a manufacturing order with *Manufacture*).
