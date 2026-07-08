No configuration is needed. Once installed:

- The product's internal reference (**default_code**) is shown next to its name on the shop listing page and on the product detail page (with the product barcode embedded as hidden GTIN metadata for SEO).
- Any product can be opened directly by its internal code using the URL `/shop/product-code/<code>`, e.g. `https://yourshop.com/shop/product-code/FURN_0001`.
- Website search (top search bar and JSON search endpoints) also matches against the product's internal code, and very short search terms (1-2 characters) are dropped automatically to keep search fast, unless every term typed is that short.
