Journal Selection Extension (Obsolete)
=====================================

This module provides specialized tools for selecting and managing accounting journals during the sales and invoicing process in Odoo. It's designed to give users more control over which journals are used for specific transactions, especially when dealing with complex invoicing scenarios or advance payments.

Key Features
============

1.  **Context-Aware Journal Selection**:
    *   Adds a dedicated wizard for selecting the **Sales Journal** and **Payment Terms** when generating invoices from a sales order.
    *   Allows users to set a specific **Currency Rate** directly in the journal selection wizard.

2.  **Smart Advance Payment Handling**:
    *   Automatically removes 'advance' products from a sales order if they haven't been invoiced yet when another product is deleted from the line items.
    *   Ensures consistent data between the sales order and the subsequent invoice.

3.  **Advanced Journal Configuration**:
    *   Allows for the configuration of a specific **Reversal Journal** directly on the accounting journal record.
    *   Integrates with Odoo's standard accounting movements to provide better traceability.

Usage
=====

1.  This module is maintained for legacy support only and is considered **Obsolete**.
2.  Navigate to **Sales > Orders** and click **Create Invoice**.
3.  In the wizard that appears, you will be able to select the target **Journal**, **Payment Terms**, and specify a custom **Currency Rate**.
4.  Configure specific **Reversal Journals** in **Accounting > Configuration > Journals**.
