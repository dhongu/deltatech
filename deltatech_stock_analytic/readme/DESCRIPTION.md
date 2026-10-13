Deltatech Stock Move Analytic
=============================

This module automates the generation of analytic account entries directly from stock movements in Odoo. It's designed for organizations that need precise tracking of costs and revenues associated with inventory transfers and adjustments.

Key Features
============

1.  **Automated Analytic Lines**:
    *   Automatically creates entries in the `account.analytic.line` model whenever a stock move reaches the 'Done' state.
    *   Captures both source and destination analytic impacts for each movement.

2.  **Location-Based Analytic Integration**:
    *   Links stock locations to specific analytic accounts.
    *   The system checks if both source and destination locations have assigned analytic accounts before creating lines, ensuring data consistency.

3.  **Valuation-Aware Postings**:
    *   Calculates the amount for analytic lines based on the unit price from the stock move, valuation layers, or the product's standard price.
    *   Includes quantities and UOM details for complete traceability.

4.  **Descriptive References**:
    *   Populates analytic line references with picking notes and names for easy identification during financial audits.

Usage
=====

1.  Navigate to **Inventory > Configuration > Locations**.
2.  Assign an **Analytic Account** to the locations you wish to track.
3.  Perform a stock movement (e.g., an internal transfer or delivery) involving these locations.
4.  Once the picking is validated and marked as **Done**, check the **Analytic Items** in Accounting to see the automatically generated lines reflecting the inventory value change.
