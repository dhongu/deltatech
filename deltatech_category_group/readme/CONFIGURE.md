Before using the grouping filters in reports, configure the available types
and classes.

**1. Grant access**

Users who will manage category groups need the **Manage category groups**
security group. By default it is implied for the Administrator role. Add
other users in *Settings > Users & Companies > Groups* if required.

**2. Define Category types**

Navigate to *Inventory > Configuration > Category options > Category types*.
Click **New**, enter a name, set the sequence (lower = higher in lists), and
save.

**3. Define Category classes**

Navigate to *Inventory > Configuration > Category options > Category classes*.
Click **New**, enter a name, set the sequence, and save.

**4. Assign types and classes to product categories**

Open any product category (*Inventory > Configuration > Product Categories*
or *Configuration > Product Categories* from any app that exposes it). On the
category form you will find two new fields, **Category type** and
**Category class**. Select the appropriate values and save.

Once categories are tagged, the group-by filters become meaningful in:

- *Inventory > Reporting > Inventory* (Stock Quant)
- Sale Margin report (requires `deltatech_sale_commission`)
- *Accounting > Reporting > Invoice Analysis*
