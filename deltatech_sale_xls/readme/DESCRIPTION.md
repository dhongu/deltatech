Customers often send their order, or the changes to it, as a spreadsheet. This module lets the
salesperson export the lines of a sales order to Excel and import them back into the same order,
with the standard Odoo export and import tools.

**Order lines button**: the **Order lines** smart button on the sales order opens the list of its
lines (**Sale Order Lines**: order, product, quantity, unit price). From this list the lines are
exported with the standard **Export**, and a file is loaded with **Import records**; the imported
lines go into this order.

**Import into an empty order**: when the order has no lines yet, every row of the file becomes a new
line of the order.

**Import into an order with lines**: when the order already has lines, each row updates the existing
line with the same product (quantity, price and the other imported columns). The product is
recognized by the internal reference between square brackets (`[CODE] Name`, as in the export) or,
failing that, by its exact name. Rows with a product that is not found or is not on the order are
skipped.

**Price formula hook**: the `use_specific_price_formula` method is called on the imported unit
prices of a new order, so a customer-specific module can apply its own price rule.

## Limitations

- When the order already has lines, a row for a new product is skipped without a message; it cannot
  add a line.
- If the order has two lines with the same product, the import of that product fails.
- Without the **Order lines** button, the order is read from the **Order Reference** column only
  when it holds the database id of the order, not its number.
