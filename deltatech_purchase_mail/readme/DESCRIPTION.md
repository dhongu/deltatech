Multi-Purchase Order Email with XLSX Summary
===========================================

This module introduces an advanced email dispatch feature for the Odoo Purchase module. It allows procurement teams to select multiple purchase orders and send them simultaneously to their respective vendors or internal stakeholders, complete with an aggregated XLSX summary and individual PDF attachments.

Key Features
============

1.  **Batch Email Dispatch**:
    *   Adds a dedicated **Send Multi Orders** action to the Purchase Order list view.
    *   Enables the simultaneous sending of multiple orders, significantly reducing manual effort for high-volume procurement operations.

2.  **Automated XLSX Summary**:
    *   Automatically generates and attaches an Excel (**XLSX**) summary containing key details from all selected purchase orders.
    *   Provides vendors or managers with a clear, aggregated overview of the procurement batch.

3.  **Individual PDF Attachments**:
    *   Ensures that the official PDF reports for each selected purchase order are attached to the outgoing email for formal acknowledgement.

4.  **Customizable Email Templates**:
    *   Uses a dedicated mail template that can be easily customized to fit corporate communication standards.

Usage
=====

1.  Navigate to **Purchase > Orders**.
2.  Select multiple Purchase Orders from the list view using the checkboxes.
3.  Click the **Action** menu and select **Send Multi Orders by Email**.
4.  Review the email composition wizard, which will already have the XLSX summary and PDFs attached.
5.  Click **Send** to dispatch the communications.
