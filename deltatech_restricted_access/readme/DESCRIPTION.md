Accounting and Valuation Restriction (Obsolete)
============================================

Status: Obsolete
================

This module is currently considered **Obsolete**. Its core functionality has been refined or incorporated into other security and valuation modules within the Deltatech suite or Odoo core.

This module was originally designed to provide specialized access control and security restrictions on accounting and inventory valuation records. It ensured that sensitive financial data and stock valuation entries were only accessible to authorized personnel.

Key Features
============

1.  **Valuation Data Security**:
    *   Designed to restrict visibility and editing of stock valuation layers and accounting entries related to inventory movements.
    *   Adds extra security groups to control access to specific financial models.

2.  **Accounting Constraints**:
    *   Integrates with Odoo's standard accounting module to enforce strict data entry rules for valuation-related accounts.

3.  **Restricted Data Editing**:
    *   Adds an **Edit sensible data** permission to the security settings.
    *   Restricts the modification of critical fields such as **Product Category Name**, **Stock Location Name**, and **Units of Measure (UOM)** to only those users with the assigned permission.

Usage
=====

1.  This module is technical and is typically installed as a dependency for legacy Deltatech configurations.
2.  Go to **Settings > Users & Companies > Users** to manage the specific security groups provided by this module.
3.  Assign the **Edit sensible data** checkbox to authorized users who need to modify critical technical data.
