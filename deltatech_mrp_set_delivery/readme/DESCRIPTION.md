Restrict Incomplete Set Deliveries
===================================

This module provides a safeguard for the delivery process of products sold as sets (Phantom BoM). It is designed to prevent the shipment of incomplete sets by ensuring that all components of a defined set are available and processed together.

Key Features
============

1.  **Phantom BoM Integration**:
    *   Adds a dedicated configuration option to **Phantom Bills of Materials (BoM)** to restrict incomplete deliveries.
    *   Ensures that Odoo's delivery system treats the components of a phantom BoM as an atomic unit for logistical purposes.

2.  **Validation Security**:
    *   Prevents the validation of a stock picking if it contains only a partial set of components for a configured phantom BoM.
    *   Reduces customer dissatisfaction and return costs by ensuring that customers always receive complete product sets.

3.  **Manufacturing Awareness**:
    *   Integrates with Odoo's core **Manufacturing (MRP)** and **Inventory (Stock)** modules to maintain strict control over set integrity during transfers.

Usage
=====

1.  Navigate to **Manufacturing > Products > Bills of Materials**.
2.  Open a BoM of type **Phantom**.
3.  Enable the **Restrict Incomplete Delivery** option (added by the module).
4.  When a sales order or transfer is created for this set, Odoo will now prevent the delivery from being validated unless all required components for the set are included in the transfer and available.
