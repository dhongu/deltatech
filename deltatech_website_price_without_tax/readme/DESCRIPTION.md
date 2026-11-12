A shop that sells to consumers and to companies usually shows prices with tax, while a company buyer wants the net price. This module adds a line with the price without tax to the product page of the website.

- **Net price line**: The price block of the product page gets a line *Price without tax* with the amount in the website currency. The line is hidden when the amount is zero.
- **Included taxes only**: The module takes the product taxes that are included in the price out of the `list_price` entry of the product price data. A tax that is not included leaves the amount unchanged, and the website display mode is not checked.
- **Display only**: The module adds a `list_price_without_tax` entry to the product price data and a template that shows it. Other prices, the cart, orders and invoices are not touched.
- **Optional view**: The line is an optional view called *Price without tax*, active after installation, which can be disabled for one website.

The module depends on Website and eCommerce (`website_sale`); every visitor sees the line. The label is written in English in the template and has a Romanian translation, *Preț fără TVA*. It reads `list_price`, not `price`, so test products that have a pricelist discount.
