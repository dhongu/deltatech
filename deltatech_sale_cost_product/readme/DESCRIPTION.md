Sale Cost on Order and Margin Tracking
======================================

This module provides specialized tools for monitoring and analyzing the costs and margins of sales orders in Odoo. It's designed for sales managers and controllers who need more visibility into the profitability of their deals at the order and order-line level.

Key Features
============

1.  **Detailed Cost Visibility**:
    *   Adds a dedicated **Purchase Cost** field directly on the Sales Order lines.
    *   Automatically populates the cost based on the product's current cost price at the time the order is created.

2.  **Margin Analysis and Hierarchy**:
    *   Integrates with Odoo's standard margin module to provide a clearer view of the profit hierarchy across sales teams.
    *   Allows users to quickly identify low-margin orders or products that are being sold below cost.

3.  **No-Code Reporting and Server Actions**:
    *   Includes pre-configured server actions for mass-updating or recalculating costs on multiple sales orders.
    *   Provides a refined security model to control which users can view or modify sensitive cost and margin data.

Usage
=====

1.  Navigate to **Sales > Orders**.
2.  Open or create a new **Sales Order** and add a product.
3.  The **Purchase Cost** field will be visible on the order line, showing the unit cost.
4.  View the calculated **Margin** for each line and the total order margin in the order footer.
5.  Use the search and filter options to identify orders with margins below a certain threshold.
