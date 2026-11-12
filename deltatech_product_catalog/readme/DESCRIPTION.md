Sales teams often need a printed catalog of the products on offer, with a picture and a code for each item. This module prints selected products, or whole eCommerce categories, as a grid of cards in a PDF.

- **Catalog from products**: The *Product Catalog* print action on products prints the selected ones, one card per product.
- **Catalog from categories**: The same action on eCommerce categories prints every product of the selected categories and their sub-categories, published or not.
- **Card content**: Each card shows the product image, internal reference, name and alternative codes. Hidden codes are left out and the list is cut after 20 characters. An underscore replaces a missing reference or code.
- **Company header and footer**: The catalog opens with the company name and address. Every page carries the company logo and address on top, and contact details, tax ID, the report footer text and page numbers at the bottom.

The module depends on *eCommerce* (`website_sale`) and *Alternative Product Codes* (`deltatech_alternative`). The print actions are not limited to a group. Prices and stock are not printed.
