Shops often give a product a special price through a fixed-price pricelist rule and want customers to see the old price crossed out. This module makes the eCommerce shop treat fixed-price rules as rules whose discount is displayed.

- **Fixed-price rules**: A pricelist rule whose computation is a fixed price tells the shop to display its discount when the rule is based on the sales price or on another pricelist. A fixed-price rule based on the cost never does, so the cost is not shown to customers. Any other rule keeps the answer given by the standard code.
- **Where it applies**: According to the code comment, the change covers the shop, the product page and the product configurators, not the cart or the checkout.
- **Price comparison**: The module does not compare prices itself. Its summary says the cut-off price appears when the fixed price is lower than the list price.
- **No configuration**: The module adds no settings, fields, screens or menus. It applies to all pricelist rules as soon as it is installed.

The module depends on *eCommerce* (`website_sale`) and needs no access rights of its own.
