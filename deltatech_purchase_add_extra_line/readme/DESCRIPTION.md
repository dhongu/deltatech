Purchase Add Extra Line Extension
=================================

This module introduces an automated process for adding extra lines (e.g., service fees, handling charges, or supplementary products) to Purchase Orders in Odoo. It's designed to help procurement teams consistently apply additional costs or items based on the primary products being purchased.

Key Features
============

1.  **Configurable Extra Products**:
    *   Allows users to define an **Extra Product** directly on the product template.
    *   Enables automated adding of this extra line whenever the primary product is added to a Purchase Order.

2.  **Flexible Pricing Logic**:
    *   The unit price for the extra line can be computed as a **percentage** of the primary product's price.
    *   If the percentage is set to zero, the system uses the standard **List Price** of the extra product.

3.  **Procurement Efficiency**:
    *   Reduces manual entry errors and ensures that all mandatory supplementary costs or items are included in every relevant Purchase Order.

Usage
=====

1.  Go to **Purchase > Products > Products**.
2.  Open a product and locate the **Extra Line Configuration** (typically in the Purchase or a dedicated tab).
3.  Select the **Extra Product** you want to associate and set the **Percentage** (if applicable).
4.  Create a new **Purchase Order** and add the primary product to the order lines.
5.  The system will automatically add the extra product as a separate line with the pre-calculated price.
