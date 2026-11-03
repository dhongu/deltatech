Loads the lines of a request for quotation from an Excel file and exports the
lines of purchase orders to Excel, so that long vendor lists do not have to be
typed by hand.

**Import of lines from Excel.** On a purchase order in the *RFQ* state, the
Actions menu (gear icon) offers **Import Purchase Line**. The wizard reads the
first sheet of an `.xlsx` file and adds one order line per row. Its options:

- **Fields**: the columns of the file, in order. The default,
  `product_code,default_code,product_name,quantity,price,uom_name`, matches the
  file produced by the export;
- **Header row**: skips the first row;
- **Search by internal code**: when the vendor code is not found, the same code
  is also searched as an internal reference;
- **Create missing product**: a product that is not found is created as a
  storable product, with a vendor price for the order vendor; otherwise the
  import stops with a message;
- **Is amount**: the price column holds the line amount, and the unit price is
  the amount divided by the quantity.

Products are found by the code in the `product_code` column, on the vendor
prices of the order vendor (for the order company or without company), then,
with **Search by internal code**, as an internal reference. A vendor code that
matches several products stops the import. When the file has no price column,
the price comes from the vendor pricelist. A unit of measure different from the
product's unit stops the import.

**Export of lines to Excel.** On one or more purchase orders, the Print menu
offers **Export Purchase Lines**, which produces `purchase_order.xlsx` with the
columns *Code* (vendor code), *Internal Code*, *Name* (vendor product name when
it exists), *Qty*, *Price* and *Unit of Measure*.

**Order lines list.** The **Order lines** smart button on the purchase order
opens the list of its lines. Importing a file there with the standard
**Import records** function updates the existing lines, matched by product;
rows whose product is not on the order are dropped. When the order has no lines
yet, the rows are created as new lines of that order.

## Limitations

- In the Excel import wizard, a row without a vendor code (`product_code`
  column) is skipped without a message, even when it has an internal code: the
  `default_code` column is read but not used to find the product. A row with a
  price that is not a number is skipped the same way.
- A quantity that is not a number, or a file without rows, makes the wizard
  fail with a technical error instead of a message.
- The wizard always adds new lines; it does not update the lines already on the
  order.
- In the **Order lines** list, an import fails when the same product is on
  several lines of the order, and works only from the list opened with the smart
  button.
