When a sales order with make-to-order products generates a request for quotation through the
procurement rules, cancelling the sales order in standard Odoo leaves the purchase lines in place.
The buyer then has to find and delete them by hand, or the products are ordered anyway.

**Purchase lines removed when the sales order is cancelled**: on **Cancel** of a sales order, the
purchase lines created for its stock moves are deleted, as long as their purchase order is still an
**RFQ** (draft). A purchase order that was already sent or confirmed is left to the buyer.

**Shared purchase lines reduced, not deleted**: when the vendor groups RFQs (**Group RFQ** set to
*Daily*, *Weekly* or *Always* on the vendor's **Sales & Purchase** tab), one purchase line can supply
several sales orders. In that case the line is kept, the cancelled moves are detached from it and
their quantity, converted to the purchase unit of measure, is subtracted from the line.

There is nothing to configure: the behaviour is active once the module is installed.

## Limitations

- Only the cancellation of the whole sales order is handled. Lowering the quantity on a confirmed
  sales order line does not change the purchase line.
- Purchase orders in **RFQ Sent** or **Purchase Order** state are not changed.
