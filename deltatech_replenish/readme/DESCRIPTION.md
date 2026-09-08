Key Features
============

Starting with Odoo 19.0 the vendor selection in the replenishment wizard is
part of the standard `purchase_stock` module: `product.replenish` inherits
`stock.replenish.mixin`, which provides the `supplier_id` field
(`product.supplierinfo`), displays it in the replenishment form and forwards it
to the procurement run as `supplierinfo_id`.

This module is therefore kept only as a compatibility placeholder for databases
upgraded from 18.0, where the feature was provided by Deltatech. It adds no
model, view or data of its own.

Features (now provided by Odoo standard):
-----------------------------------------

- A "Vendor" field in the product replenishment wizard.
- Selection of a specific vendor from the list of product suppliers.
- The selected vendor is used when the replenishment creates a purchase order.
- The vendor lead time is taken into account for the scheduled date.

Usage:
------

1. Go to Inventory > Products or any view where the "Replenish" button is available.
2. Click on "Replenish" for a product.
3. Pick a route that buys the product; the "Vendor" field is displayed.
4. Select the desired supplier and proceed with the replenishment.
