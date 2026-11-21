# Deltatech Delivery Status

This module extends the functionality of the delivery system in Odoo to provide enhanced tracking and status management for shipments.

## Features

- Adds detailed delivery status tracking to stock pickings
- Lets you postpone and release the deliveries of a sales order
- Lets sales teams postpone the deliveries of their orders paid by wire transfer
- Extends payment providers with a Postponed Delivery option
- Keeps the carrier status of the parcel on the delivery, updated by the shipping integrations
- Enables monitoring of delivery status throughout the logistics process
- Improves communication between sales, warehouse, and customers regarding shipment status
- Centralizes delivery information for better visibility across the organization

## Delivery Blocking Features

- **Manual Delivery Blocking**: Allows users to manually postpone deliveries by marking pickings as postponed
- **Payment Provider Based Blocking**: Automatically postpones deliveries based on payment provider configuration
  - Each payment provider can be configured with the "Postponed Delivery" option
  - When enabled, deliveries are automatically blocked when the order is confirmed before the payment is done
  - Once payment is confirmed, the system automatically releases the blocked deliveries
- **Sales Team Configuration**: Sales teams can be configured to postpone the deliveries of the orders paid by wire transfer
  - Special handling for wire transfers, allowing businesses to verify payment before shipping; these deliveries are released manually, from the order
- **Order-level Management**: Provides functions to postpone or release deliveries at the sales order level
- **Status Visibility**: Shows the postponed status on pickings (ribbon and field) and, on orders, through the Release button and the Postponed delivery filter

## Delivery State Tracking

The module introduces a comprehensive `delivery_state` field on stock pickings that tracks the package's journey through the entire logistics process:

- **Draft**: Initial state when the delivery is just created
- **Ready in warehouse**: The package is prepared and waiting in the company's warehouse
- **Pre advice**: The delivery note/AWB has been generated but the carrier hasn't picked up the package yet
- **In Transit**: The package has been picked up by the carrier and is on its way
- **In Carrier Warehouse**: The package has arrived at the carrier's sorting facility/warehouse
- **In delivery**: The package is out for final delivery to the customer
- **Delivered**: The package has been successfully delivered to the customer
- **Refused**: The customer refused the package

This granular state tracking provides several benefits:

- Allows customer service to give precise information about delivery status
- Helps identify bottlenecks in the logistics process
- Enables better coordination between warehouse operations and delivery carriers
- Provides data for analytics on delivery performance and efficiency
- Improves customer experience with more accurate delivery status information

The module also adds an `available_state` field that visually indicates the availability status of products in pickings:

- **Available**: All products are available and ready for delivery
- **Partially available**: Some products are available, but not all
- **Unavailable**: The products are not reserved (for transfers delivered all at once, also when they are only partially reserved)

This module is essential for businesses that need to closely monitor the status of their deliveries and want to provide accurate tracking information to their customers. It enhances the standard Odoo delivery system by adding more granular status tracking, payment-dependent delivery control, and better integration between the sales, warehouse, and payment processes.
