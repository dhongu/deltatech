Product Reordering Limits and Inventory Status
============================================

This module introduces a simplified way to manage inventory replenishment levels directly on the product template in Odoo. It's designed for inventory managers who need to maintain specific minimum and maximum stock levels globally for a product, without the complexity of individual reordering rules for every warehouse location.

Key Features
============

1.  **Template-Level Reordering Limits**:
    *   Adds **Total Minimum** and **Total Maximum** quantity fields directly to the product template form.
    *   Allows users to define replenishment thresholds that apply to the entire product (including all its variants).

2.  **Inventory Status Monitoring**:
    *   Automatically calculates whether a product is currently **Below Minimum** based on the total quantity available in all internal stock locations.
    *   Adds a dedicated search filter to the product view, allowing users to quickly identify all items that require replenishment.

3.  **Unified Stock Awareness**:
    *   Provides a high-level view of inventory health, making it easier to manage procurement and production for complex catalogs.

Usage
=====

1.  Navigate to **Inventory > Products > Products**.
2.  Open any product record and locate the **Reordering Limits** section (typically in the Inventory or General Information tab).
3.  Define the **Total Minimum** and **Total Maximum** quantities you wish to maintain in stock.
4.  In the product list view, use the **Below Minimum** search filter to see which items are currently under their defined replenishment threshold.
5.  Use this information to trigger new purchase or manufacturing orders.
