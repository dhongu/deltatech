Logistic Documents Centralizer
==============================

This module provides a centralized repository for logistical and shipping-related documentation within Odoo. It's designed to streamline the management of physical documents (like CMRs, certificates of origin, or delivery notes) across different stages of the supply chain.

Key Features
============

1.  **Unified Documentation Hub**:
    *   Adds a dedicated **Logistics Documents** view that aggregates attachments from various models.
    *   Tracks documents related to **Sales Orders**, **Purchase Orders**, **Stock Pickings**, and **Invoices** in a single place.

2.  **Smart Linking**:
    *   Automatically identifies and links documents based on the logical flow of Odoo documents (from Order to Picking to Invoice).
    *   Allows logistics teams to quickly access all relevant files for a specific shipment or transaction.

3.  **Document Categorization**:
    *   Supports tagging and categorizing logistical files for easier filtering and searching during audits.

Usage
=====

1.  Navigate to **Inventory > Configuration > Logistics Documents** (or a similar menu entry added by the module).
2.  Use the search and filter options to find documents related to a specific **Partner**, **Order**, or **Picking**.
3.  Upload new logistical files directly to the relevant document (Sales Order, Picking, etc.), and they will appear in the central viewer.
4.  Download or view attachments for verification during the shipping and delivery process.
