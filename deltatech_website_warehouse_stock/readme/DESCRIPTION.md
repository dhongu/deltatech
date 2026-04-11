This module enhances the eCommerce experience by providing real-time stock availability for each warehouse directly on the product page. Customers can see if a product is in stock, low on stock, or unavailable at specific locations, helping them make informed purchasing decisions based on warehouse proximity or availability.

While Odoo 18/19 introduced a standard "Click & Collect" feature with a map-based store selector, this module provides a complementary, high-visibility approach:
- **Direct visibility**: Stock status is displayed statically on the product page, eliminating the need for clicks or popups.
- **Stock Thresholds**: Uses configurable thresholds to display "Available" instead of exact numbers for high stock levels, protecting inventory data and brand image.
- **Simplified Setup**: Enable stock display per warehouse with a single checkbox, without complex shipping method configurations.

Features:

- Adds the stok of the main stock location of every warehouse to the product template page in website.
- If the stock is < 0 it will display "Out of stock" on that warehouse.
- If the stock is 0<x<=10 it will display the stock of the product.
- If the stock is > 10 it will display "Available" on that warehouse
- The value 10 is the default value for the stock threshold and it is configurable in site settings
- The name for the warehouse displayed in warehouse is the same of the name in the warehouse form.
- There is a check in the warehouse to choose if the stock is displayed in the product template page.

Future Development & Integration:
This module is specifically designed to function as an **informative addon** that complements the standard Odoo 18/19 "Click & Collect" (`website_sale_collect`) feature. While the standard Odoo flow is optimized for the checkout process (map selector, pickup point selection), this module adds value by providing:
- **Instant Awareness**: Customers see stock distribution before even starting the checkout process.
- **Data Protection**: Prevents competitors from knowing exact stock levels via the threshold system.
- **Enhanced UX**: Reduces friction by providing all necessary availability data directly on the product page.

Migration to Odoo 19:
The module has been updated to follow Odoo 19 standards and best practices:
- **Manifest**: Version updated to 19.0.
- **Python Models**: Added type hints for better code clarity and IDE support.
- **Configuration**: Updated `res.config.settings` to use the modern `<setting>` tag in XML views, replacing older label/div structures.
- **QWeb Templates**: Replaced `t-esc` with `t-out` for better security and performance in line with Odoo's latest recommendations. Updated XPath selectors to match Odoo 19's redesigned product page structure and configuration views (moved distribution info to `o_wsale_product_details_content` inside `o_wsale_product_details_content_section`, and updated configuration XPath to target the new `setting` tag).
- **Data Types**: Refined system parameter handling (threshold) to ensure consistent data type processing.
