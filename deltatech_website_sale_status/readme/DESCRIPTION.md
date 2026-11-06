The standard order status (Quotation, Sales Order, Cancelled) does not tell a shop
customer, or the sales team, where the order is: waiting for stock, ready to ship,
with the courier or delivered. This module adds a **Stage** field on the sales
order, computed from the order, its transfers and the courier status, and shows it
in the back office and in the customer portal.

**Order stage**: computed and stored on each order, with tracking in the chatter:

- **Placed**: a website quotation sent to the customer (only with the detailed stage
  option, see below).
- **In Process**: the order is being handled by the sales team.
- **Request for Quotation**: a confirmed order with nothing to pick yet, whose
  purchase RFQ was sent to the vendor (only when *sale_purchase* is installed).
- **Waiting availability**: a transfer of the order is waiting for stock.
- **Postponed**: the delivery was postponed (the *Postponed delivery* flag of the
  order transfers).
- **To Be Delivery**: the goods are available and the order can be shipped.
- **Pre advice**: an AWB was generated for the parcel (detailed stage only).
- **In Delivery**: the parcel is with the courier.
- **Delivered**: all the transfers are done, or, with the detailed stage, the courier
  delivered the parcel.
- **Canceled**: the order was cancelled.

Website carts that were never sent have no stage.

**Detailed order stage**: an option in **Sales > Configuration > Settings**,
*Invoicing* section, *Detailed order stage* (off by default). Off, the order is
**Delivered** when its transfers are validated. On, a website quotation sent is
**Placed** and, after validation, the stage follows the courier status of the parcel
(**Pre advice**, **In Delivery**) until the courier delivers it. Only the transfers
validated in the last 30 days are followed.

**Back office**: the stage appears as a coloured badge in the quotation and order lists
and on the order form, next to the payment terms. The order search gets the filters
**Placed**, **In process** and **To Be Delivery**, and a **Phone** search on the
customer. The stage is also available in the sales analysis report.

**Customer portal**: in *My Account > Sales Orders*, the order list shows the stage as
a badge and can be filtered by **Open Orders**, **Closed Orders** or by each stage, and
sorted by **Order Stage**. The **Canceled** and **Closed Orders** filters also list the
cancelled orders. The pager keeps the selected filter.

**Unpaid Orders**: the standard eCommerce *Unpaid Orders* action also lists the
confirmed website orders that are not fully paid.

## Limitations

- The **Returned** value exists in the stage list but no rule sets it: a returned
  order is not shown as such.
- In Odoo 20 the *Unpaid Orders* action has no menu; it opens only from a link or a
  custom menu.
- The *Unpaid Orders* domain uses the payment status field added by the module
  *deltatech_sale_payment*, which is not a dependency. Without that module the action
  raises an error.
