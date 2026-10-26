Adds an **Import Lines** button on requests for quotation (draft and
sent purchase orders) that loads the order lines from a file with the
wizard of `deltatech_import_lines`.

- Besides the internal reference, barcode and name, products can be
  matched by **Vendor Product Code**: the code from the vendor
  pricelist of the order vendor (or of its company), in the order
  company.
- Only products that can be purchased are matched.
- The unit price comes from the vendor pricelist, as for a line added by
  hand, unless the file has a **Unit Price** or **Discount** column
  mapped.

Installed automatically when both Purchase and `deltatech_import_lines`
are installed.
