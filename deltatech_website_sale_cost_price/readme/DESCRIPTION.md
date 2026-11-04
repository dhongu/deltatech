This module extends the standard eCommerce option **Prevent Sale of Zero Priced Product**: the shop
also stops selling a product when its price is lower than its cost price plus a minimum margin.

For such a product the customer no longer sees the price and the **Add to Cart** button, but the
**Contact Us** button (the same behaviour as for zero priced products), and the cart button disappears
from the product list.

Key features:

- **Cost price protection**: the website price (after the website pricelist) is compared with the
  product cost (**Cost** field).
- **Minimum margin**: a margin percentage set on the website (with 10%, the price must be at least
  110% of the cost).
- **Tax aware**: the cost (kept without taxes) is increased with the taxes when the website displays
  prices with taxes.
- **Currency conversion**: the cost is converted to the website currency.
