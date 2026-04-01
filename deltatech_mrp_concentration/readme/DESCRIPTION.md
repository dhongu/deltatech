MRP Concentration Management
============================

This module introduces a specialized concentration management feature for manufacturing processes in Odoo. It's designed for industries (such as chemical, food, or pharmaceuticals) where the actual concentration of an active ingredient in a component can vary, requiring adjustments in the production quantities to maintain final product quality.

Key Features
============

1.  **Component Concentration Tracking**:
    *   Adds a **Concentration** field directly on the Bill of Materials (BoM) lines.
    *   Allows manufacturing engineers to specify the required concentration of each raw material or ingredient.

2.  **Dynamic Production Adjustments**:
    *   Integrates with Odoo's core **Manufacturing (MRP)** module to ensure that the actual quantities consumed during production account for the specified concentration.
    *   Ensures consistent quality and potency of the finished goods by compensating for variations in component concentrations.

3.  **Traceability and Documentation**:
    *   Includes concentration data in both the BoM and the individual Manufacturing Orders (MO) for better auditability and quality control.

Usage
=====

1.  Navigate to **Manufacturing > Products > Bills of Materials**.
2.  Open or create a BoM and locate the **Concentration** field in the component lines.
3.  Enter the required concentration percentage for each active component.
4.  Create a **Manufacturing Order** for this BoM.
5.  View the resulting concentration and quantity information on the MO to ensure production accuracy.
