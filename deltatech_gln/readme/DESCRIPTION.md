Partner GLN (Obsolete)
======================

.. IMPORTANT::

   This module is currently considered **Obsolete**. Its core functionality has been moved to and is now better served by the `account_add_gln` module.

This module was originally designed to provide specialized handling for Global Location Numbers (GLN) for partners within Odoo. It ensured that GLN data was correctly stored and synchronized for electronic data interchange (EDI) and logistical processes.

Key Features
============

1.  **GLN Field Integration**:
    *   Adds a dedicated **GLN (Global Location Number)** field to the partner form view.
    *   Ensures that GLN data is easily accessible and editable for each business location.

2.  **Compatibility Layer**:
    *   Acts as a bridge for legacy configurations that require the `deltatech_gln` dependency.
    *   Supports the migration of GLN data to the newer `account_add_gln` standard.

Usage
=====

1.  No new configuration is required for this module as it is obsolete.
2.  If you have this module installed, ensure that `account_add_gln` is also active in your system for correct GLN handling.
3.  New projects should directly use the `account_add_gln` module instead of this one.
