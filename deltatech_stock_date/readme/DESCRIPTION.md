Stock Account Date Redirection (Obsolete)
========================================

Status: Obsolete
================

This module is currently considered **Obsolete**. Its core functionality has been moved to and is now better served by the `l10n_ro_stock_account_date` module.

This module was originally designed to provide more granular control over the accounting dates of stock valuation entries. It ensured that inventory valuation postings matched the intended fiscal period, especially during month-end closes.

Key Features
============

1.  **Valuation Date Synchronization**:
    *   Designed to ensure the accounting date of valuation entries matches the stock movement date.
    *   Integrates with Odoo's stock accounting module to manage the period in which inventory assets are valued.

2.  **Compatibility Wrapper**:
    *   Acts as a bridge for legacy configurations where `deltatech_stock_date` was a required dependency.
    *   Ensures a smooth transition to the newer `l10n_ro_stock_account_date` implementation.

Usage
=====

1.  No new configuration is required for this module as it is obsolete.
2.  If you have this module installed, ensure that `l10n_ro_stock_account_date` is also active in your system for correct Romanian accounting date handling on stock moves.
3.  New projects should directly use the `l10n_ro_stock_account_date` module instead of this one.
