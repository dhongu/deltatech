An order may need more of a product than its warehouse holds, while another warehouse of the company has some. On confirmation, this module prepares a transfer from the other warehouse for the missing quantity.

- **Check on confirmation**: Confirming a sales order checks each storable product line against the stock of the order's warehouse. Services and other non-storable products are ignored.
- **Transfer for the shortfall**: One transfer per order moves the missing quantity from the other warehouse to the order's warehouse, for no more than the other warehouse holds, and is reserved at once.
- **Type and grouping**: *Type auto transfer* on the other warehouse sets the operation type (its internal type when empty). *Group Transfer With Delivery* on the order's warehouse groups the transfer with the order's delivery.
- **Traceability**: The transfer gets a note linking to the order, and the order gets a message naming the transfer.
- **Automatic validation**: When *Auto Confirm Transfer* is on for the other warehouse (the `confirm_transfer` context key overrides it), the transfer is validated at once. If its products cannot all be reserved, an error stops the order confirmation.

It depends on `sale_stock`. Only the first other warehouse of the company is used as the source. The warehouse form of this version does not show *Auto Confirm Transfer*.
