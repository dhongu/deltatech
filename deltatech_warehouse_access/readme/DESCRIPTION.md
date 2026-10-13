Warehouse Access
================

This module provides more granular control over warehouse operations by restricting access to specific users.

Features
========

1.  **User-Based Warehouse Restriction**:
    *   Adds a dedicated **Users** tab in the Warehouse configuration view.
    *   Allows administrators to define a list of authorized users for each warehouse.

2.  **Validation Security**:
    *   Prevents unauthorized users from validating stock pickings associated with a restricted warehouse.
    *   Raises a clear `Access Error` if a user attempts to validate a picking without the necessary permissions.

3.  **Flexible Access Rules**:
    *   If no users are specified in the **Users** tab of a warehouse, the default Odoo access rights apply (everyone with stock permissions can access it).
    *   Once at least one user is added, access is strictly limited to the defined list.

Usage
=====

1.  Navigate to **Inventory > Configuration > Warehouses**.
2.  Open the desired warehouse record.
3.  Go to the **Users** tab (available in developer mode or for users with appropriate technical rights).
4.  Add the users who should have permission to validate operations for this warehouse.
5.  Save the changes.
