Deltatech Product Extension
===========================

This module expands the standard Odoo product model by introducing essential technical and logistical fields. It's designed for businesses that require detailed tracking of product attributes like shelf life, manufacturer details, and physical dimensions.

Key Features
============

1.  **Enhanced Logistical Tracking**:
    *   Adds **Shelf Life** and **Unit of Measure for Shelf Life** fields to the product template.
    *   Allows for better management of perishable or time-sensitive inventory.

2.  **Detailed Manufacturer Information**:
    *   Integrates a link to the **Manufacturer** (Partner) directly on the product form.
    *   Provides quick access to manufacturing origin and contact details.

3.  **Physical Dimensions**:
    *   Adds a free-text **Dimensions** field to the product, for example "120 x 60 x 75 cm".
    *   Useful for documents, catalogs and quick reference. The field does not calculate the product volume. For numeric Length, Width and Height fields that fill in the volume, use the Product Dimensions module (`deltatech_product_dimension`).

4.  **Partner Integration**:
    *   Extends the partner model to include a "Manufacturer" checkbox, allowing for easy categorization of vendors and suppliers.

Usage
=====

1.  Go to **Sales > Products > Products** or **Inventory > Products > Products**.
2.  Open any product record. **Manufacturer** appears under the product category; **Dimensions** and **Shelf Life** appear in the **General Information** tab, next to the cost.
3.  Fill in the **Manufacturer**, **Shelf Life**, and its **UOM**.
4.  Enter the **Dimensions** as text (for example L x W x H) as needed for your documents or catalog.
5.  In the **Contacts** module, you can now tag partners as manufacturers for better filtering.
