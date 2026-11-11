A shop that sells to consumers and to companies usually shows prices with tax, while a company buyer wants the net price. This module adds a line with the price without tax to the product page of the website.

- **Net price line**: The price block of the product page gets a muted line *Preț fără TVA:* (Romanian for "price without VAT") with the amount in the website currency. The line is hidden when the amount is zero.
- **Follows the display mode**: When the website shows prices tax excluded, the line repeats the displayed price. Otherwise the product taxes are taken out of the displayed price, as if every tax were included in it.
- **Display only**: The module adds a `list_price_without_tax` entry to the product price data and a template that shows it. Other prices, the cart, orders and invoices are not touched.
- **Optional view**: The line is an optional view called *Product Price without tax*, active after installation, which can be disabled for one website.

The module depends on Website and eCommerce (`website_sale`); every visitor sees the line. The label is written in Romanian in the template and has no translation. The amount comes from the `list_price` entry, not from `price`, so test products that have a pricelist discount.
