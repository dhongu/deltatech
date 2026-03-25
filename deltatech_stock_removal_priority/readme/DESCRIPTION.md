Stock Removal Location by Priority
=================================

This module introduces a priority-based stock removal strategy for Odoo warehouse locations. It is designed to give inventory managers more granular control over the order in which items are picked from different storage areas, ensuring optimal logistical flows and storage utilization.

Key Features
============

1.  **Priority-Based Picking Strategy**:
    *   Adds a dedicated removal strategy called **Priority** to the stock location configuration.
    *   Allows users to assign specific priority levels to different warehouse locations.
    *   Ensures that Odoo automatically selects stock from the highest priority locations first during the picking process.

2.  **Optimized Logistics Flow**:
    *   Ideal for warehouses that have preferred picking zones or need to prioritize stock removal from specific areas (e.g., forward picking zones over backup storage).
    *   Reduces travel time for warehouse pickers by ensuring stock is pulled from the most accessible locations first.

3.  **Seamless Stock Integration**:
    *   Integrates with Odoo's standard inventory management and removal strategy framework.

Usage
=====

1.  Navigate to **Inventory > Configuration > Locations**.
2.  Assign a **Removal Priority** (integer value) to the relevant stock locations.
3.  Go to **Inventory > Configuration > Product Categories**.
4.  Set the **Removal Strategy** for the desired product categories to **Priority**.
5.  Create a stock movement (picking) for a product in that category.
6.  The system will automatically suggest picking items from the locations with the highest priority first.
