## 19.0.1.0.0 (2026-10-12)

- Migrated to Odoo 19.
- The flow is enabled per sales journal (*Delivery from invoice*). Up to 18.0 it ran on every customer
  invoice; when upgrading, the option is checked on all the sales journals, so the behaviour stays the same.
- The discount of the invoice line is copied to the sale order line, and the order line stays linked to the
  invoice line.
- The lines without a sale order always go to a new order. Up to 18.0 they could be added to an existing order
  of the customer, which was then not delivered.
- The delivery keeps the reserved quantities: every move with a demand is delivered in full. The 18.0 code
  deleted the moves that already had a quantity, so those products were not delivered.
- When the stock is not enough, the message lists each product with the available and the requested quantity.
- The delivery is refused, with a clear message, for warehouses that deliver in more than one step.
- A negative quantity is returned by the standard Odoo 19 flow; the custom stock rule override was removed.
- The delivery takes the accounting date of the invoice, so that the sale and the cost of the goods sold
  fall in the same period.
- Own module icon, in the flat style of the other invoice modules, instead of the generic gears.
