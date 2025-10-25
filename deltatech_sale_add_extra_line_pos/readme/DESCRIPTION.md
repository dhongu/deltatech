# Sale Add Extra Line - Point of Sale Extension

The **deltatech_sale_add_extra_line_pos** module is an Odoo addon that extends the Point of Sale (POS) functionality to automatically add extra product lines to POS orders based on configured products. This module is a specialized extension of the `deltatech_sale_add_extra_line` module, specifically designed for the Point of Sale system.

## Features

- **Real-time POS Integration**: Seamlessly integrates automatic extra line addition directly into the Point of Sale interface
- **Client-side Processing**: Handles extra product addition on the client side for immediate visual feedback
- **Dynamic Quantity Calculation**: Automatically calculates and updates extra product quantities based on the main product quantities in the POS cart
- **Product Configuration**: Allows configuration of extra products and quantity multipliers directly in the product template
- **Automatic Line Consolidation**: Intelligently consolidates multiple extra product lines into a single line with the correct total quantity
- **Real-time Updates**: Updates extra product quantities instantly when main product quantities are modified in the POS cart

## How It Works

### Product Configuration

In the product template, you can configure:
- **Extra Product**: The product that should be automatically added when the main product is sold
- **Extra Quantity Multiplier**: A multiplier to calculate how much of the extra product should be added (e.g., 0.1 means 10% of the main product quantity)

### POS Workflow

1. **Adding Products**: When a cashier adds a product with extra product configuration to the POS cart, the system automatically adds the configured extra product as a separate line

2. **Quantity Adjustment**: When the quantity of the main product is modified, the extra product quantity is automatically recalculated based on:
   - All instances of products that reference the same extra product
   - The quantity multiplier configured for each product
   - The formula: `Extra Qty = Σ(Main Product Qty × Extra Qty Multiplier)`

3. **Line Consolidation**: If an extra product is referenced by multiple products in the cart, the module consolidates them into a single line with the aggregated quantity

4. **Session Processing**: When the POS session is closed, the extra product information is properly transferred to the backend for order processing

## Use Cases

This module is particularly useful for retail and hospitality businesses that need to:

- **Environmental Fees**: Automatically add environmental or recycling fees based on product types
- **Bag Charges**: Add shopping bag charges based on the number or volume of products purchased
- **Service Charges**: Include service or handling fees for certain product categories
- **Packaging Materials**: Automatically account for packaging materials used per product
- **Deposit Fees**: Add deposit charges for returnable containers or bottles
- **Transaction Fees**: Include payment processing or transaction fees

## Technical Implementation

The module extends the Point of Sale system through:

- **JavaScript Patches**: Extends POS order and order line models using Odoo's patch mechanism
- **Client-side Logic**: Implements automatic extra line addition and quantity calculation in the POS interface
- **Backend Integration**: Ensures proper synchronization of extra product information between frontend and backend
- **Product Template Extension**: Adds extra product fields to the product template model
- **Session Handling**: Properly loads extra product configuration data when POS sessions are opened

## Benefits

- **Improved Accuracy**: Eliminates manual errors in adding fees or related products
- **Faster Checkout**: Reduces time spent manually adding extra items
- **Consistency**: Ensures uniform application of fees and charges across all transactions
- **Transparency**: Customers can clearly see extra charges itemized on their receipt
- **Compliance**: Helps meet regulatory requirements for separate fee disclosure
- **Efficiency**: Cashiers can focus on customer service rather than remembering to add extra items

## Dependencies

This module depends on:
- `deltatech_sale_add_extra_line` - The base module for extra line functionality
- `point_of_sale` - Odoo's Point of Sale module

## Integration

The module works seamlessly with Odoo's standard POS features and can be combined with other POS extensions for enhanced functionality.
