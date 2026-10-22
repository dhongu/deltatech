Features:

- prints labels from products, sale orders, pickings, lots and quants
- default layouts with product name, internal reference, barcode, lot and price including VAT (with currency and
  unit of measure), for shop shelves, warehouses or products, each with its own paper format:
  - A4 sheet of 3x8 labels (70x37 mm), for any office printer
  - 100x50 mm and 40x25 mm, one label per page, for thermal printers
  - continuous labels, without a paper format
- the wizard proposes the layout printed last by the user; the first time, the A4 3x8 sheet
- if only lot option is selected and printing is started from a product, all lots in stock will be printed
- by default overrides the print label button in products. To revert to standard print function, system parameter
  "terrabit_labels.override_print_button" must be set to False
- custom layouts can be created by defining a report on the product.product.label model
- the ZPL layouts (report type text) have a Preview button: the ZPL is sent to the Labelary service
  (api.labelary.com) and returned as PDF. The label size is set on the report (Label width / height, Printer
  resolution) or read from its name, e.g. "Labels 40x30 ZPL (300 DPI)"
