Invoice Weight and Mass Tracking
===============================

This module adds logistical weight tracking capabilities directly to Odoo's invoicing and order management systems. It's designed to help businesses monitor and report on the total net and gross weight of items being invoiced, purchased, or sold.

Key Features
============

1.  **Weight Fields on Documents**:
    *   Adds **Net Weight** and **Gross Weight** fields to Invoices, Purchase Orders, and Sales Orders.
    *   Automatically calculates total document weights based on the items included.

2.  **Reporting and Analysis**:
    *   Enables weight-based reporting in the Invoice analysis view.
    *   Supports **Pivot** table views, allowing users to aggregate weights by partner, product, or period.
    *   Provides weight information on the printed invoice report for logistical transparency.

3.  **Cross-Document Consistency**:
    *   Ensures weight data is maintained and transferred accurately between sales/purchase documents and the final invoice.

Usage
=====

1.  Navigate to **Sales > Orders**, **Purchase > Orders**, or **Accounting > Customer Invoices**.
2.  Open or create a new document.
3.  The **Net Weight** and **Gross Weight** fields will be visible, showing calculated totals for the document.
4.  To perform a weight analysis, go to **Accounting > Reporting > Invoices**.
5.  Switch to the **Pivot** view and add the weight fields to your measures for a detailed breakdown.
