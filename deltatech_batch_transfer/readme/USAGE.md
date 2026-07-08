1. From a **Sale Order** (or a list of sale orders for the same customer) use the **Prepare Batch** action to open the wizard; it pre-fills the customer and mode (Sale/Purchase).
2. Set the **Responsible** user, an optional **Reference**, and whether to **Set Done Quantity** directly.
3. Optionally add specific products and quantities in the wizard lines to only pick those products; leave empty to include all available quantities for the customer's/vendor's ready pickings.
4. Confirm to create a new batch transfer, attach the matching outgoing (Sale) or incoming (Purchase) pickings in `waiting`/`confirmed`/`assigned` state, confirm the batch, and check availability.
5. When validating the batch, pickings with all quantities at zero ("empty" pickings) are automatically removed from the batch instead of being processed — unless the system parameter `deltatech_batch_keep_pickings` is set, in which case they stay in the batch for later processing (not recommended for the barcode interface).
6. The batch also exposes **Direction**, **Reference** and **Note** fields for better tracking.
