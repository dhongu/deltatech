Extends the standard **Receipt Status** of the purchase order
(`receipt_status`: Not Received, Partially Received, Fully Received),
computed by Odoo from the receipts:

- the status is shown by default in the requests for quotation and purchase
  orders lists;
- search filters *Receipt in Progress*, *Partially Received* and *Fully
  Received*, and grouping by receipt status;
- the status changes are tracked in the chatter of the order.

Up to version 19 the module computed its own *Delivery Status* (Done / In
Progress). On upgrade, saved filters, export templates and grouping on the old
field are moved to the standard receipt status.
