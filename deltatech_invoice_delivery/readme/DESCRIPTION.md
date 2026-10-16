Deliver the goods straight from the customer invoice: when an invoice is posted, the storable products
are added to a sale order, the order is confirmed and the delivery is validated, in one step and without
a separate quotation.

- **One step**: posting the invoice creates the sale order, confirms it and delivers the goods from stock.
- **Enabled per journal**: only the sales journals with *Delivery from invoice* checked use the flow, so the
  invoices issued from sale orders keep the standard behaviour.
- **Only what needs a delivery**: services and lines already linked to a sale order are left as they are.
- **Same values as the invoice**: quantity, unit, price, discount and taxes are copied to the order line, which
  stays linked to the invoice line, so the order is shown as delivered and invoiced.
- **Stock check before posting**: when the stock is not enough, the invoice is not posted and the message lists
  each product with the available and the requested quantity.
- **Returns on the same invoice**: a line with a negative quantity brings the goods back to stock.
