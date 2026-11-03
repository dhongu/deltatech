Companies that price their products as cost plus a fixed percentage need a
place to keep that percentage on each product. This module adds a **Trade
Markup** field to products. It stores the markup only; it does not compute
any price by itself.

**Trade Markup field.** A **Trade Markup** field (a percentage) is added on
the product form, in the *General Information* tab, next to *Sales Price*
and *Cost*. It is shared by all the variants of a product, and its changes
are logged in the product chatter.

**Base for other modules.** The field is used by the Terrabit module
`deltatech_purchase_price`, which recomputes the sales price from the last
purchase price and the trade markup and offers a wizard to set the markup on
several products at once. Install that module if you want the sales price to
follow the markup automatically.

## Limitations

- Installed alone, this module does not change the sales price: the markup
  is informative until a module such as `deltatech_purchase_price` uses it.
