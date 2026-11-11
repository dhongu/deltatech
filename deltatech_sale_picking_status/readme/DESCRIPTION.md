Sales teams need to see which sales orders still have deliveries to make. This module builds on the standard delivery status of sales orders and makes it easier to show, filter and follow.

- **Standard status**: The module adds no status of its own. It works on the standard `delivery_status` field of the sales order and leaves its values and calculation unchanged.
- **List column**: The delivery status shows by default as a column in the quotation and order lists, as a colored badge in the quotation list.
- **Filters and grouping**: Three search filters, *Delivery in Progress*, *Partially Delivered* and *Fully Delivered*, select orders by delivery status. *Delivery in Progress* covers the pending, started and partial values. A *Delivery Status* group-by option is added next to the customer one.
- **Chatter tracking**: Each change of the delivery status is tracked in the order's chatter.

The module depends on `sale_stock` and `mail_tracking` and adds no groups, so anyone who can see sales orders sees the status. On upgrade from earlier versions, saved filters and export templates that used the former own status are rewritten on the standard one.
