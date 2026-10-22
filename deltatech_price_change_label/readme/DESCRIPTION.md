Adds a **Print Labels** button to the price change document. It opens the product labels wizard of
`deltatech_product_labels` with one line for each product of the document, so the shelf labels of
all the products with a new price can be printed at once.

The module adds the **Shelf label with price** layout (product name, price including taxes, code
and unit of measure), proposed by default from the document; any other label layout can be chosen.

The module installs by itself when both `deltatech_price_change` and `deltatech_product_labels`
are installed.
