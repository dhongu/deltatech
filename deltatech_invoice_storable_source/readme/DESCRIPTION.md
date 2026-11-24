Keeps stock and invoicing in step: storable products are invoiced only from a sale order and billed
only from a purchase order, so every invoiced storable line has an order behind it, with its delivery
or receipt. Set the invoicing policy to *Delivered quantities* to invoice only what was delivered.

- **Customer invoices**: a customer invoice, credit note or sales receipt with a storable product that
  does not come from a sale order cannot be posted.
- **Vendor bills**: a vendor bill, refund or purchase receipt with a storable product that does not come
  from a purchase order cannot be posted.
- **Every way of posting**: the *Confirm* button, the mass confirmation from the list and the scheduled
  auto-posting are all checked. Point of Sale invoices are not checked.
- **Services pass**: services (transport, labour etc.) and goods without *Track Inventory* are not
  checked.
- **Credit notes from an order**: a credit note or refund reversing an invoice issued from an order
  keeps the link to the order and is posted normally.
- **Per company**: the two checks are enabled separately, in *Invoicing / Accounting → Configuration →
  Settings*, in the *Customer Invoices* and *Vendor Bills* sections.
