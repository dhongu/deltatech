Buyers who receive goods in several deliveries need to see which purchase orders are still waiting for goods. This module builds on the standard receipt status of purchase orders and makes it easier to show, filter and follow.

- **Standard status**: The module adds no status of its own. It works on the standard `receipt_status` field of the purchase order and leaves its values and calculation unchanged.
- **List column**: The receipt status column is shown by default in the RFQ and purchase order lists.
- **Filters and grouping**: Three search filters, *Receipt in Progress*, *Partially Received* and *Fully Received*, select orders by receipt status. *Receipt in Progress* covers orders that are pending or partially received. A *Receipt Status* group-by option is added next to the vendor one.
- **Chatter tracking**: Each change of the receipt status is tracked in the order's chatter.

The module depends on `purchase_stock` and `mail_tracking` and adds no groups, so anyone who can see purchase orders sees the status. On upgrade from earlier versions, saved filters and export templates that used the former own status are rewritten on the standard one.
