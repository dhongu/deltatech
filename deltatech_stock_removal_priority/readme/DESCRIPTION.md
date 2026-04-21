Stock Removal Location by Priority
===================================

This module introduces a priority-based stock removal strategy for Odoo warehouse locations. It gives inventory managers granular control over the order in which items are picked from different storage areas, ensuring optimal logistical flows and storage utilization.

Designed to work together with **deltatech_putaway_strategy**: putaway rules direct products to specific sub-locations at receipt, and this module uses those same rules to determine the removal order at picking time.

Key Features
============

1. **Priority-Based Picking Strategy**:
   - Adds a dedicated removal strategy called **Priority** to the stock location configuration.
   - Ensures that Odoo automatically selects stock from the highest priority locations first during the picking process.

2. **Automatic Priority from Putaway Rules**:
   - The removal priority for each stock quant is automatically derived from existing **putaway rules**.
   - Rules are matched first by product, then by product category.
   - A configurable default priority can be set via system parameters (default: 999).

3. **Always Up-to-Date Priorities**:
   - When a putaway rule is created, modified, or deleted, the removal priority of all affected quants is automatically recalculated.
   - No manual intervention required.

4. **Exclude Locations Support**:
   - Specific locations can be excluded from stock gathering during picking operations.

5. **Optimized for Large Warehouses**:
   - Ideal for warehouses with preferred picking zones or multiple storage tiers.
   - Reduces picker travel time by ensuring stock is pulled from the most accessible locations first.

Usage
=====

1. Navigate to **Inventory > Configuration > Locations**.
2. Configure **Putaway Rules** with appropriate sequence values — lower sequence = higher priority.
3. Go to **Inventory > Configuration > Product Categories**.
4. Set the **Removal Strategy** for the desired product categories to **Priority**.
5. Create a stock movement (picking) for a product in that category.
6. The system will automatically suggest picking items from the highest priority locations first.

Configuration
=============

- To set a custom default priority, go to **Settings > Technical > System Parameters** and set the key ``stock.removal_priority.default`` to the desired integer value (default: 999).
