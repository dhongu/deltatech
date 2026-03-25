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
    *   Adds fields for specifying product dimensions (Length, Width, Height) directly on the product record.
    *   Useful for shipping, storage planning, and catalog displays.

4.  **Partner Integration**:
    *   Extends the partner model to include a "Manufacturer" checkbox, allowing for easy categorization of vendors and suppliers.

Usage
=====

1.  Go to **Sales > Products > Products** or **Inventory > Products > Products**.
2.  Open any product record and locate the new fields in the **General Information** or a dedicated **Technical** tab.
3.  Fill in the **Manufacturer**, **Shelf Life**, and its **UOM**.
4.  Enter the **Dimensions** (L x W x H) as needed for your logistics or cataloging.
5.  In the **Contacts** module, you can now tag partners as manufacturers for better filtering.
