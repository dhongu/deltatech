Adds an **Import Lines** button on quotations (draft and sent sale
orders) that loads the order lines from a file with the wizard of
`deltatech_import_lines`.

- Only products that can be sold are matched.
- The unit price, the taxes and the description come from the
  pricelist and the product, as for a line added by hand. When the file
  has a **Unit Price** or **Discount** column mapped, its values are used
  instead.
- The unit of measure from the file must be related to the unit of the
  product.

Installed automatically when both Sales and `deltatech_import_lines`
are installed.
