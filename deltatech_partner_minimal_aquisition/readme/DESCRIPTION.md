Partner Minimal Acquisition Validation
======================================

This module provides a safeguard for the procurement process by enforcing a minimum purchase value for specific partners. It's designed to help businesses comply with vendor-imposed minimum order requirements, reducing the risk of order rejections and administrative overhead.

Key Features
============

1.  **Vendor-Specific Minimums**:
    *   Adds a **Minimal Purchase Value** field to the partner form view (Purchase tab).
    *   Allows procurement managers to define different minimum order thresholds for each supplier.

2.  **Proactive Validation**:
    *   Automatically checks the total amount of a Purchase Order against the partner's minimum value during the confirmation process.
    *   Triggers a clear warning message as a banner if the order total is below the required threshold, allowing the user to adjust the order before proceeding.

3.  **Procurement Efficiency**:
    *   Ensures that every confirmed purchase order meets the vendor's economic criteria, streamlining the supply chain communication.

Usage
=====

1.  Navigate to **Purchase > Vendors**.
2.  Open a vendor record and go to the **Purchase** tab.
3.  Set the **Minimal Purchase Value** for this supplier.
4.  Create a new **Purchase Order** for this vendor.
5.  If you try to confirm an order with a total amount less than the defined minimum, the system will display a warning banner, prompting you to increase the quantities or add more products.
