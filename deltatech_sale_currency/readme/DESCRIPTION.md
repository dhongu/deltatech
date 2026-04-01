Sale Currency Extension
=======================

This module provides specialized handling for currency conversion between sales orders and their generated invoices. It's particularly useful for businesses that maintain pricelists in one currency (e.g., EUR) but wish to issue invoices in another (e.g., the journal's currency or company's functional currency like RON).

Key Features
============

1.  **Journal-Based Invoice Currency**:
    *   Automatically sets the currency of the generated invoice based on the selected sales journal's currency.
    *   Overrides Odoo's default behavior of using the sales order's currency for the invoice.

2.  **Automatic Price Conversion**:
    *   Converts unit prices from the sales order's currency to the invoice's currency during the invoicing process.
    *   Uses the exchange rate valid on the date of the conversion.
    *   Ensures that financial records in the accounting journal reflect the correct values in the desired currency.

3.  **Cross-Module Integration**:
    *   Seamlessly integrates with both the **Sales** and **Accounting** modules to ensure a consistent data flow.

Usage
=====

1.  Create a **Sales Order** using a pricelist in a specific currency (e.g., USD).
2.  Ensure a **Sales Journal** with a different currency (e.g., EUR) is associated with the sales order or configured as the default.
3.  Confirm the sales order and click **Create Invoice**.
4.  The system will automatically convert the product prices from USD to EUR based on the current exchange rate and set the invoice's currency to EUR.
