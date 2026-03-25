Deltatech Purchase Discount
===========================

This module introduces a simplified way to manage discounts directly on purchase order lines in Odoo. It's designed to help procurement managers easily record and apply percentage-based discounts to individual products without needing complex pricing rules.

Key Features
============

1.  **Direct Discount Entry**:
    *   Adds a **Discount %** field to the purchase order lines.
    *   Adds a **Price without Discount** (List Price) field to store the initial price from the vendor.

2.  **Automated Unit Price Calculation**:
    *   Automatically recomputes the **Unit Price** whenever the base price or the discount percentage is modified.
    *   Ensures that the final cost for each line accurately reflects the applied discount.

3.  **Procurement Visibility**:
    *   Allows users to see at a glance both the original vendor price and the discounted price for each item on the order.

Usage
=====

1.  Navigate to **Purchase > Orders**.
2.  Open or create a new **Purchase Order**.
3.  Add a product to the order lines.
4.  Enter the vendor's original price in the **Price without Discount** field.
5.  Enter the agreed **Discount %** (e.g., 10%).
6.  The system will automatically update the **Unit Price** to reflect the 10% reduction.
