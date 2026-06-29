# Deltatech Discount Policy

This module restores the Odoo 17 discount policy functionality in Odoo 18, allowing users to choose how discounts are displayed on sales orders.

## Features

- **Restore Discount Policy Selection**: Adds the `discount_policy` field to the Pricelist, giving you the choice between:
    - **Discount included in the price**: The unit price on the sales order line will be the final discounted price, and the discount field will be set to 0.
    - **Show public price & discount to the customer**: The unit price will show the public (base) price, and the discount percentage will be explicitly shown.
- **Fixed Price Rule Support**: Restores the Odoo 17 behavior for fixed price rules. When using the "Show public price & discount" policy, the module calculates the equivalent discount percentage even for fixed price rules, ensuring the customer sees the original price and the applied discount.
- **Pricelist Rule Chain Traversal**: Correctly identifies the base price by traversing the pricelist rule chain, mirroring the logic available in Odoo 17.
- **Improved Transparency**: Provides better flexibility in how pricing is presented to customers, which was changed in the standard Odoo 18 release.

This module is particularly useful for businesses that migrated from Odoo 17 and want to maintain their existing pricing presentation or for those who prefer the Odoo 17 way of handling fixed price discounts on sales documents.
