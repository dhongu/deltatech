When the own stock is not enough, the salesperson wants to know whether the vendor can still supply
the product, and whether another warehouse of the company has it. This module records the stock
reported by the vendor and shows it, together with the free stock per warehouse, on the sales order.

**Vendor stock on the vendor pricelist**: adds **Quantity Available** on the vendor pricelist line
(`product.supplierinfo`), on the form and as an optional column of the list, for example in the
**Vendors** list of the product. The vendor stock of a product is the sum of these quantities over
its vendor lines; a line set on a specific variant counts only for that variant.

**Vendor stock on the sales order line**: the availability popover of the order line (the chart icon
next to the quantity) shows a **Vendor Stock** row when the vendor has stock, converted to the unit of measure of the line.
**Vendor Quantity Available** is also available as an optional column of the order lines.

**Coloured availability icon**: the chart icon of the order line is coloured by availability:
green when the demand will be fulfilled, cyan when it will be fulfilled but there is no free
quantity today, red when it will not be fulfilled, yellow when it will not be fulfilled but the
vendor has stock.

**Free stock per warehouse**: when the company has more than one warehouse, the popover lists the
free stock in each warehouse with stock, the warehouse of the order first, and opens the forecast
report of that warehouse on click. The same information is available in the optional
**Stock/WH** column of the order lines.

## Configuration

- Fill in **Quantity Available** on the vendor lines of the products, by hand or by import.
- The colours of the icon are set in **Sales > Configuration > Settings**, in the
  **Quotations & Orders** section.
- The system parameter `deltatech_vendor_stock.use_only_main_location` set to `1` limits the free
  stock per warehouse to the main stock location of each warehouse.

## Limitations

- **Other Quantity Available** (the **Other Stock** row of the popover) is not filled in by this
  module; it stays 0 unless another module computes it.
- The vendor stock adds up the vendor lines of all the companies selected in the company switcher,
  not only those of the current company and its parent companies.
