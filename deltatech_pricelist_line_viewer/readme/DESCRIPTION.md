Price List Line Viewer
======================

This module enhances Odoo's pricelist management by providing a dedicated list view for pricelist items (lines). This makes it significantly easier to search, filter, and manage complex pricing rules across multiple products and categories.

Key Features
============

1.  **Centralized Pricelist Line View**:
    *   Adds a convenient box button at the top of the pricelist form view.
    *   Clicking the button opens a full-screen tree view containing all pricing rules for that specific pricelist.

2.  **Advanced Searching and Filtering**:
    *   Enables standard Odoo searching and filtering capabilities on pricelist lines.
    *   Provides much easier access and management for pricelists with large numbers of rules.

3.  **Refined Security Controls**:
    *   Introduces a new technical group: **Permit pricelist editing**.
    *   Allows designated users to modify pricelists and their lines without requiring full Sales Administrator privileges.

Usage
=====

1.  Navigate to **Sales > Products > Pricelists**.
2.  Open any pricelist record.
3.  Click the new **Pricelist Items** (or similarly named) button in the stat button area at the top of the form.
4.  Interact with the tree view to find, filter, or edit the specific pricing rules you need.
5.  Assign the **Permit pricelist editing** group to users who should manage pricing without full administrative access.
