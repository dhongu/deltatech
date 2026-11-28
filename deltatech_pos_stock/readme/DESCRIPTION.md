This module extends the Point of Sale functionality to display the stock quantity and the price directly on the product cards.

Key features:

- Shows the stock quantity of the register's warehouse for each product, updated live.
- Shows product price on the same badge.
- Stock and price information is displayed as a badge on the product image.
- Toggle stock and price visibility through POS settings.
- Choose, per register, whether the badge shows the stock on hand or the available quantity
  (stock minus everything already reserved for other operations: deliveries, internal
  transfers, manufacturing).
- Products with nothing left show the quantity in red; adding one to the order raises a
  warning but does not block the sale.
- Compatible with the Odoo 19 OWL architecture.
- Only displays stock for storable products.
