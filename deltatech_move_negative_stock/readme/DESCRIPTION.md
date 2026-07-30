Replenish Negative Stock
========================

This module provides a convenient way to identify and resolve negative inventory levels at specific stock locations by automatically populating transfers with required quantities from other source locations.

Key Features
============

1.  **Automated Negative Qty Identification**:
    *   Adds a dedicated **Get negative products** button to the stock picking form.
    *   Automatically identifies all products with a negative quantity in the destination location of the current picking.

2.  **Effortless Transfer Population**:
    *   Quickly adds lines to the current transfer for all identified negative stock items.
    *   Populates the move lines with the exact quantities needed to bring the destination inventory back to at least zero.

3.  **Stock Health Monitoring**:
    *   Designed for inventory managers who need to maintain clean, non-negative stock records across multiple locations.
    *   Streamlines the process of internal stock replenishment and correction.

4.  **Daily Notification**:
    *   Each internal location can be assigned a **Manager**.
    *   A daily scheduled action emails the manager the list of products with negative stock in that location, aggregated over its sub-locations.
    *   Locations without a manager are skipped.

Usage
=====

1.  Create or open an internal **Stock Picking** (Transfer).
2.  Set the **Source Location** and **Destination Location** as needed.
3.  Click the **Get negative products** button in the header of the transfer.
4.  The system will scan the destination location for any negative inventory.
5.  Move lines will be automatically created or updated to include the necessary quantities to fix the negative levels.
6.  Validate the picking as usual to complete the replenishment.
7.  Optionally, set a **Manager** on the location to receive the daily negative stock email.
