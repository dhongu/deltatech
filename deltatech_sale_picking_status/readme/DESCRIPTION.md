Extends the standard **Delivery Status** of the sales order
(`delivery_status`: Not Delivered, Started, Partially Delivered, Fully
Delivered), computed by Odoo from the delivery orders:

- the status is shown by default in the quotations and sales orders lists;
- search filters *Delivery in Progress*, *Partially Delivered* and *Fully
  Delivered*, and grouping by delivery status;
- the status changes are tracked in the chatter of the order.

Up to version 19 the module computed its own *Picking Status* (Done / In
Progress). On upgrade, saved filters, export templates and grouping on the old
field are moved to the standard delivery status.
