# Sale Add Extra Line Module

The **deltatech_sale_add_extra_line** module is an Odoo addon that provides automated functionality for adding extra product lines to sale orders based on the products being sold.

## Features

- **Automatic Extra Line Addition**: Automatically adds an extra line for configured products in sale orders
- **Product Configuration**: The product added in the extra line can be configured in the product template
- **Smart Price Calculation**: The unit price of the extra line is computed from the percent configured in the product. If the percent is zero, the standard price computation applies, so the extra line gets the price of its own product in the pricelist, currency and unit of measure of the order
- **Manual Price Override**: A unit price typed in on the extra line is kept and no longer recomputed from the main line. The quantity keeps following the main line. To go back to the computed price, delete the extra line — it is regenerated automatically
- **Quantity-based Calculation**: The quantity of the extra product is calculated based on the quantity of the main product and a configurable multiplier
- **Point of Sale Integration**: Works seamlessly with both regular sale orders and Point of Sale transactions

## How It Works

1. **Product Configuration**: In the product template, you can configure:
   - An extra product that should be automatically added
   - A percentage for price calculation
   - A quantity multiplier for the extra product

2. **Automatic Addition**: When a product with extra product configuration is added to a sale order, the system automatically:
   - Adds the configured extra product as a new line
   - Calculates the appropriate quantity based on the main product quantity
   - Sets the price based on the configured percentage or list price

3. **Dynamic Updates**: When quantities of main products are modified, the extra product quantities are automatically recalculated and updated accordingly

## Use Cases

This module is particularly useful for:
- **Service Charges**: Automatically adding service fees based on product sales
- **Mandatory Accessories**: Adding required accessories or complementary products
- **Packaging Materials**: Adding packaging costs based on product quantities
- **Installation Services**: Adding installation or setup services for certain products
- **Warranty Extensions**: Automatically including warranty products

## Technical Implementation

The module extends the standard Odoo sale order functionality by:
- Adding fields to product templates for extra product configuration
- Overriding sale order line creation methods to trigger extra line addition
- Implementing quantity and price calculation logic
- Providing Point of Sale integration through JavaScript patches

This automation helps businesses ensure consistency in their sales processes and reduces manual errors when adding related products or services to customer orders.
