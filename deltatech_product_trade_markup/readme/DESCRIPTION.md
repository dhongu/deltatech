Product Trade Markup and Pricing
================================

This module introduces an automated pricing mechanism for Odoo products based on a trade markup percentage. It's designed to help businesses maintain consistent profit margins by automatically calculating the selling price from a base cost or purchase price.

Key Features
============

1.  **Cost-Based Selling Price Calculation**:
    *   Adds a **Trade Markup Percent** field to the product template and variant forms.
    *   Automatically computes the **List Price** (Selling Price) based on the product's cost and the defined markup.

2.  **Flexible Foundation**:
    *   Allows choosing between different base prices for the markup calculation (e.g., Cost Price or Last Purchase Price).
    *   Handles price updates dynamically whenever the cost price or the markup percentage changes.

3.  **Consistency Monitoring**:
    *   Ensures that selling prices across the product catalog follow a standardized markup logic, reducing the risk of manual pricing errors.

Usage
=====

1.  Navigate to **Sales > Products > Products**.
2.  Open a product and go to the **Sales** or **Inventory** tab.
3.  Set the **Trade Markup Percent** (e.g., 20%).
4.  The system will automatically calculate the **List Price** based on the product's **Cost**.
5.  If the cost is updated, the selling price will be re-evaluated to maintain the 20% markup.
