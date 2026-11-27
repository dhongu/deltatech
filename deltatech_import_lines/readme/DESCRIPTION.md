Loads the lines of a document from a spreadsheet or a text file, straight
from the document, without the generic import screen. The wizard reads
**XLSX**, **XLS**, **ODS**, **CSV** and **TXT** files (the separator of
CSV and TXT files is detected or set by hand) with the readers of the
standard import.

This module holds the wizard and the saved mappings. The documents are
added by the bridge modules, installed automatically with their
application:

- `deltatech_import_lines_sale`: quotations;
- `deltatech_import_lines_purchase`: requests for quotation, also by
  vendor product code;
- `deltatech_import_lines_stock`: receipts, deliveries, internal
  transfers and inventory counts;
- `deltatech_import_lines_mrp`: components of manufacturing orders.

Features:

- **Column mapping**: each file column is imported as product, quantity,
  unit price, discount, unit of measure, lot/serial number or
  description, or ignored. Columns with the usual titles (Code, Quantity,
  Price, UoM, Lot…) are mapped automatically.
- **Product matching** by internal reference, barcode or name (the
  `[CODE] Name` display format is resolved by the code).
- **Preview** of every row with its status: found, product not found,
  several products, invalid quantity or number, invalid unit of measure,
  lot/serial error. The import is blocked while there are errors, unless
  **Skip Rows With Errors** is ticked.
- **Saved mappings** per document type and, optionally, per partner. The
  wizard proposes the mapping of the partner first, then the generic one
  of the document type.
- Numbers written with a decimal comma or a decimal point are accepted.
- The lines are created through the document itself, so prices, taxes,
  descriptions and the other computed values are filled as when the line
  is added by hand. The unit price and the discount are taken from the
  file only when their columns are mapped.
