1. Open the document (quotation, request for quotation, transfer or
   manufacturing order) and click **Import Lines**. For an inventory count,
   open **Inventory > Operations > Physical Inventory** and click
   **Import Counts**.
2. Select the file. Check **Header Row** when the first row holds the
   column titles, choose how the products are matched (**Match Product
   By**) and, if needed, a **Saved Mapping**. Click **Next**.
3. In the column list, set **Import As** for each column to import; leave
   it empty for the columns to ignore. A product and a quantity column are
   required.
4. Optionally, fill in **Mapping Name** (and **Only For This Partner**) and
   click **Save Mapping**, so the next file of the same layout is mapped
   automatically. With an empty name, the selected mapping is updated.
5. Click **Preview**. The rows with errors are shown in red with the
   reason. Fix the file and go **Back**, or tick **Skip Rows With
   Errors**.
6. Click **Import**. The lines are added to the document.

The saved mappings can be reviewed under **Configuration > Import Line
Mappings** in Sales, Purchase and Inventory.

Numbers are read with a decimal comma or a decimal point. A single comma is
always the decimal separator: `1,5` is one and a half, and `1,234` is
read as one point two three four, not as one thousand two hundred
thirty-four. Save files that use the
comma as thousands separator with a decimal point (`1,234.00`) or without
thousands separators.
