Base Pricelist on Cost with VAT
===============================

This module provides a specialized pricing strategy for Odoo pricelists, allowing businesses to base their selling prices on product costs including VAT. It is designed for retail and wholesale environments where pricing decisions are often made relative to the total acquisition cost (tax included).

Key Features
============

1.  **VAT-Inclusive Cost Calculation**:
    *   Adds a technical field to the product model that computes the **Cost with VAT**.
    *   Automatically identifies and applies the default purchase tax for the product to its standard cost.

2.  **Dynamic Pricelist Foundation**:
    *   Allows pricelist items to reference the VAT-inclusive cost as a base for markups or discounts.
    *   Ensures that selling prices consistently reflect the desired profit margin over the total tax-included cost.

3.  **Cross-Module Integration**:
    *   Seamlessly integrates Odoo's core **Sales**, **Product**, and **Accounting** modules for accurate tax-aware pricing.

Usage
=====

1.  Navigate to **Sales > Products > Products**.
2.  Ensure that each product has a **Cost** and a **Purchase Tax** assigned.
3.  Go to **Sales > Configuration > Pricelists**.
4.  Create or open a pricelist and add a rule.
5.  Set the **Base** for the calculation to **Cost with VAT** (if available) or use the calculated field in your pricing rules.
6.  Selling prices will now be dynamically computed based on the tax-included acquisition cost.
